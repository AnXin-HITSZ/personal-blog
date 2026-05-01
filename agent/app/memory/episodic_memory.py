import json
import time
import math
import sqlite3
import os
import uuid

import jieba
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.memory.utils.tokenizer import jieba_tokenizer, STOPWORDS


@dataclass
class MemoryItem:
    """
    统一的记忆数据结构
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "user"
    content: str = ""
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_timestamp(self) -> datetime:
        """
        将时间戳转换为人类可读的日期时间格式
        """
        return datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典，方便存入 SQLite
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "importance": self.importance,
            "timestamp": self.timestamp,
            "metadata": json.dumps(self.metadata, ensure_ascii=False)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """
        从 SQLite 字典恢复
        """
        if isinstance(data.get("metadata"), str):
            data["metadata"] = json.loads(data["metadata"])
        return cls(**data)

@dataclass
class MemoryConfig:
    """
    配置类
    """
    database_path: str = "./episodic_memory.db"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "episodic_memory"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    memory_capacity: int = 1000
    vector_weight: float = 0.6
    keyword_weight: float = 0.4
    time_decay_half_life_days: float = 7.0

class SQLiteDocumentStore:
    """
    轻量级 SQLite 文档存储
    """
    def __init__(self, db_path: str = "./episodic_memory.db"):
        """
        初始化数据库连接
        """
        self.db_path = db_path
        self._conn = None

        self._connect()

        self._create_table()

    def _connect(self):
        """
        建立数据库连接
        """
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def _create_table(self):
        """
        创建记忆表
        """
        cursor = self._conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories(
                id TEXT PRIMARY KEY,            -- 记忆唯一 ID
                role TEXT NOT NULL,             -- 角色(user / assistant)
                content TEXT NOT NULL DEFAULT '', -- 记忆内容
                importance REAL DEFAULT 0.5,    -- 重要性(0.0 - 1.0)
                timestamp REAL NOT NULL,        -- 时间戳
                metadata TEXT NOT NULL          -- 元数据(JSON 字符串)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')

        self._conn.commit()
        print("[SQLite] 数据库初始化完成")

    def add_document(self, doc: Dict[str, Any]):
        """
        添加一条记忆文档到数据库
        """
        cursor = self._conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO memories
            (id, role, content, importance, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            doc["id"],
            doc["role"],
            doc["content"],
            doc["importance"],
            doc["timestamp"],
            doc["metadata"]
        ))

        self._conn.commit()

    def get_documents_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        根据 ID 列表批量获取记忆文档
        """
        if not ids:
            return []

        placeholders = ', '.join('?' for _ in ids)

        cursor = self._conn.cursor()
        cursor.execute(f'''
            SELECT id, role, content, importance, timestamp, metadata
            FROM memories
            WHERE id IN ({placeholders})
        ''', ids)

        return [dict(row) for row in cursor.fetchall()]

    def get_all_ids(self) -> List[str]:
        """
        获取数据库中所有记忆的 ID（按时间升序排列）
        """
        cursor = self._conn.cursor()
        cursor.execute('SELECT id FROM memories ORDER BY timestamp ASC')
        return [row[0] for row in cursor.fetchall()]

    def get_count(self) -> int:
        """
        获取数据库中记忆的总条数
        """
        cursor = self._conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM memories')
        return cursor.fetchone()[0]

    def delete_document(self, doc_id: str):
        """
        根据 ID 删除一条记忆
        """
        cursor = self._conn.cursor()
        cursor.execute('DELETE FROM memories WHERE id = ?', (doc_id,))
        self._conn.commit()

class LocalEmbeddingModel:
    """
    本地 Embedding 模型
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化模型
        """
        self.model = None
        self.vector_size = 384

        try:
            if not os.environ.get("HF_ENDPOINT"):
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

            repo_id = f"sentence-transformers/{model_name}" if "/" not in model_name else model_name

            model_path = None
            from huggingface_hub import snapshot_download
            import time as _time

            try:
                cached_path = snapshot_download(repo_id, local_files_only=True)
                # 验证缓存是否完整（检查模型权重文件）
                has_weights = any(
                    os.path.isfile(os.path.join(cached_path, f))
                    for f in os.listdir(cached_path)
                    if f.endswith((".safetensors", ".bin"))
                )
                if has_weights:
                    print(f"[Embedding] 从缓存加载模型: {model_name}")
                    model_path = cached_path
                else:
                    print(f"[Embedding] 缓存不完整，清理并重新下载...")
                    import shutil
                    shutil.rmtree(cached_path)
            except Exception:
                pass

            if model_path is None:
                try:
                    from modelscope.hub.snapshot_download import snapshot_download as ms_download
                    print(f"[Embedding] 首次加载模型: {model_name} (~80MB)")
                    print(f"[Embedding] 正在从 ModelScope 下载...")
                    _start = _time.time()
                    model_path = ms_download(repo_id)
                    _elapsed = _time.time() - _start
                    print(f"[Embedding] 下载完成，耗时 {_elapsed:.1f} 秒")
                except ImportError:
                    print(f"[Embedding] 首次加载模型: {model_name} (~80MB)")
                    print(f"[Embedding] 正在从 {os.environ['HF_ENDPOINT']} 下载...")
                    _start = _time.time()
                    model_path = snapshot_download(repo_id, local_files_only=False)
                    _elapsed = _time.time() - _start
                    print(f"[Embedding] 下载完成，耗时 {_elapsed:.1f} 秒")

            self.model = SentenceTransformer(model_path)
            self.vector_size = self.model.get_embedding_dimension()
            print(f"[Embedding] 模型加载成功！向量维度: {self.vector_size}")
        except Exception as e:
            print(f"[Embedding] 模型加载失败: {e}")
            print("[Embedding] 将使用随机向量进行测试")

    def embed(self, text: str) -> List[float]:
        """
        将单个文本转换为向量
        """
        if self.model is not None:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            return list(np.random.randn(self.vector_size).astype(np.float32))

def create_embedding_model_with_fallback() -> LocalEmbeddingModel:
    return LocalEmbeddingModel()

class QdrantVectorStore:
    """
    Qdrant 向量数据库
    """

    def __init__(
            self,
            url: str = "http://localhost:6333",
            api_key: str = "",
            collection_name: str = "episodic_memory",
            vector_size: int = 384
    ):
        """
        初始化 Qdrant 连接
        """
        self.collection_name = collection_name
        self.vector_size = vector_size

        self.client = QdrantClient(
            url=url,
            api_key=api_key if api_key else None
        )

        self._create_collection_if_not_exists()
        print(f"[Qdrant] 连接成功，集合: {collection_name}")

    def _create_collection_if_not_exists(self):
        """
        如果集合不存在则创建
        """
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"[Qdrant] 创建新集合: {self.collection_name}")

    def add_vector(self, vector_id: str, vector: List[float], payload: Dict[str, Any]):
        """
        添加一条向量及其元数据
        """
        point = PointStruct(
            id=uuid.UUID(vector_id),
            vector=vector,
            payload=payload
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def search(
            self,
            query_vector: List[float],
            limit: int = 10,
            filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索与查询向量最相似的向量
        """
        qdrant_filter = None
        if filter_criteria:
            must_conditions = []
            for key, value in filter_criteria.items():
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            qdrant_filter = Filter(must=must_conditions)

        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=limit
        )

        results = []
        for hit in hits.points:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            })
        return results

    def delete_vector(self, vector_id: str):
        """
        根据 ID 删除一条向量
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[uuid.UUID(vector_id)]
        )

class EpisodicMemory:
    """
    情景记忆
    """

    def __init__(self, config: MemoryConfig):
        self.config = config

        self.doc_store = SQLiteDocumentStore(config.database_path)
        self.embedding = LocalEmbeddingModel(config.embedding_model_name)
        self.vector_store = QdrantVectorStore(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key,
            collection_name=config.qdrant_collection_name,
            vector_size=self.embedding.vector_size
        )

        self.sessions: Dict[str, List[str]] = {}
        self._tfidf_cache: Dict[str, Any] = {}

        self._rebuild_session_index()

    def _rebuild_session_index(self):
        """
        从 SQLite 恢复所有会话记忆索引
        """
        all_ids = self.doc_store.get_all_ids()
        if not all_ids:
            return
        docs = self.doc_store.get_documents_by_ids(all_ids)
        for doc in docs:
            item = MemoryItem.from_dict(doc)
            sid = item.metadata.get("session_id", "default")
            if sid not in self.sessions:
                self.sessions[sid] = []
            self.sessions[sid].append(item.id)

    def add(self, item: MemoryItem) -> str:
        """
        新增单条记忆
        """
        session_id = item.metadata.get("session_id", "default")
        item.metadata["session_id"] = session_id

        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(item.id)

        self.doc_store.add_document(item.to_dict())

        vec = self.embedding.embed(item.content)
        self.vector_store.add_vector(
            vector_id=item.id,
            vector=vec,
            payload={
                "session_id": session_id,
                "timestamp": item.timestamp,
                "importance": item.importance
            }
        )

        if session_id in self._tfidf_cache:
            del self._tfidf_cache[session_id]

        return item.id

    def add_episode(
            self,
            session_id: str,
            role: str,
            content: str,
            importance: float = 0.5,
            **kwargs
    ) -> str:
        """
        快捷新增记忆
        """
        item = MemoryItem(
            role=role,
            content=content,
            importance=importance,
            metadata={"session_id": session_id, **kwargs},
        )
        return self.add(item)

    def _load_memories_by_ids(self, ids: List[str]) -> List[MemoryItem]:
        """
        根据 ID 批量读取记忆对象
        """
        rows = self.doc_store.get_documents_by_ids(ids)
        return [MemoryItem.from_dict(r) for r in rows]

    def _tfidf_score(self, query: str, memories: List[MemoryItem]) -> Dict[str, float]:
        """
        批量计算 TF-IDF 文本相似度
        """
        if len(memories) < 2:
            return {}

        session_id = memories[0].metadata.get("session_id", "default")
        cache_key = session_id

        if cache_key in self._tfidf_cache and self._tfidf_cache[cache_key]["cnt"] == len(memories):
            vectorizer = self._tfidf_cache[cache_key]["vec"]
            tf_mat = self._tfidf_cache[cache_key]["mat"]
        else:
            contents = [m.content for m in memories]
            vectorizer = TfidfVectorizer(
                tokenizer=jieba.lcut,
                token_pattern=None,
                stop_words=list(STOPWORDS)
            )
            tf_mat = vectorizer.fit_transform(contents)
            self._tfidf_cache[cache_key] = {
                "vec": vectorizer,
                "mat": tf_mat,
                "cnt": len(memories)
            }

        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, tf_mat)[0]
        return {memories[i].id: float(sims[i]) for i in range(len(memories))}

    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """
        计算关键词匹配分数: 匹配词数 / 总查询词数，反映查询词在记忆中的覆盖率
        """
        if not query or not content:
            return 0.0

        query_words = jieba.lcut(query.lower())
        content_words = jieba.lcut(content.lower())

        def is_valid_word(w: str) -> bool:
            return len(w) >= 1 and w not in STOPWORDS and w.strip() != ""

        query_words_filtered = [w for w in query_words if is_valid_word(w)]
        content_words_set = set([w for w in content_words if is_valid_word(w)])

        if not query_words_filtered:
            return 0.0

        matched_words = [w for w in query_words_filtered if w in content_words_set]
        matched_count = len(matched_words)
        score = matched_count / len(query_words_filtered)

        if matched_words:
            print(f"[匹配] 查询: {query} | 记忆: {content[:40]}... | 匹配词: {matched_words} | 分数: {score:.2f}")

        return score

    def _calc_time_decay(self, ts: float, half_life_days: float) -> float:
        """
        计算记忆时间衰减分数
        """
        age_days = (time.time() - ts) / 86400
        decay = math.exp(-age_days / half_life_days)
        return max(decay, 0.01)

    def retrieve(
            self,
            query: str,
            limit: int = 5,
            session_id: Optional[str] = None
    ) -> List[Tuple[float, MemoryItem]]:
        """
        混合检索: 语义向量 + TF-IDF 关键词 + 时间衰减 + 重要性
        """
        candidate_ids = self.sessions.get(session_id, []) if session_id else self.doc_store.get_all_ids()
        if not candidate_ids:
            return []

        candidates = self._load_memories_by_ids(candidate_ids)
        if not candidates:
            return []

        q_vec = self.embedding.embed(query)
        filter_dict = {"session_id": session_id} if session_id else None
        vector_hits = self.vector_store.search(q_vec, limit=limit * 3, filter_criteria=filter_dict)
        vec_score_map = {h["id"]: h["score"] for h in vector_hits}

        tfidf_map = self._tfidf_score(query, candidates)

        result_list = []
        for mem in candidates:
            s_score = vec_score_map.get(mem.id, 0.0)
            t_score = tfidf_map.get(mem.id, 0.0)
            k_score = self._calculate_keyword_score(query, mem.content)
            text_score = t_score * 0.7 + k_score * 0.3

            base = (
                s_score * self.config.vector_weight
                + text_score * self.config.keyword_weight
            )

            decay = self._calc_time_decay(mem.timestamp, self.config.time_decay_half_life_days)
            imp_weight = 0.8 + (mem.importance * 0.4)

            final_score = base * decay * imp_weight
            if final_score > 0.001:
                result_list.append((final_score, mem))

        result_list.sort(key=lambda x: x[0], reverse=True)
        return result_list[:limit]
