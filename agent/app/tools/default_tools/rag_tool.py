import os
import glob
import threading
import uuid
import io
import time
from typing import Dict, Any, List, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from app.tools.base import Tool, ToolParameter


class _RAGEmbedding:
    """
    Embedding 模型封装
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None
        self.vector_size = 384

        repo_id = f"sentence-transformers/{model_name}" if "/" not in model_name else model_name
        print(f"[RAG] 加载嵌入模型: {model_name}")

        try:
            self.model = SentenceTransformer(repo_id)
            self.vector_size = self.model.get_embedding_dimension()
            print(f"[RAG] 模型加载成功，向量维度: {self.vector_size}")
        except Exception as e:
            print(f"[RAG] 模型加载失败: {e}")

    def embed(self, text: str) -> List[float]:
        if self.model is not None:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        return list(np.random.randn(self.vector_size).astype(np.float32))


class _RAGVectorStore:
    """
    向量存储封装
    """

    def __init__(self, url: str, api_key: str, collection_name: str, vector_size: int):
        self.collection_name = collection_name
        self.vector_size = vector_size

        self.client = QdrantClient(url=url, api_key=api_key if api_key else None)
        self._create_collection_if_not_exists()
        print(f"[RAG] Qdrant 连接成功，集合: {collection_name}")

    def _create_collection_if_not_exists(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )
            print(f"[RAG] 创建新集合: {self.collection_name}")

    def add_vector(self, vector_id: str, vector: List[float], payload: Dict[str, Any]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=uuid.UUID(vector_id), vector=vector, payload=payload)]
        )

    def search(self, query_vector: List[float], limit: int = 10,
               filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        qdrant_filter = None
        if filter_criteria:
            must_conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filter_criteria.items()]
            qdrant_filter = Filter(must=must_conditions)

        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=limit
        )

        return [{"id": h.id, "score": h.score, "payload": h.payload} for h in hits.points]

    def count(self) -> int:
        try:
            return self.client.count(collection_name=self.collection_name, exact=True).count
        except Exception:
            return 0


def create_rag_pipeline(
    qdrant_url: str,
    qdrant_api_key: str,
    collection_name: str,
    rag_namespace: str,
    knowledge_base_path: str = ""
) -> Dict[str, Any]:
    """
    创建 RAG 管道，返回包含嵌入模型和向量存储的配置字典
    """
    print(f"[RAG] 创建管道: namespace={rag_namespace}, collection={collection_name}")

    embedding = _RAGEmbedding("all-MiniLM-L6-v2")

    vector_store = _RAGVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name,
        vector_size=embedding.vector_size
    )

    pipeline = {
        "embedding": embedding,
        "vector_store": vector_store,
        "collection_name": collection_name,
        "namespace": rag_namespace,
    }

    if knowledge_base_path:
        _index_knowledge_base(knowledge_base_path, pipeline)

    print(f"[RAG] 管道 {rag_namespace} 创建完成")
    return pipeline

def _index_knowledge_base(knowledge_base_path: str, pipeline: Dict[str, Any]):
    """
    扫描知识库目录，将文档转换为 Markdown 后分块、嵌入并存入 Qdrant
    """
    if not os.path.isdir(knowledge_base_path):
        print(f"[RAG] 知识库路径不存在: {knowledge_base_path}")
        return

    embedding: _RAGEmbedding = pipeline["embedding"]
    vector_store: _RAGVectorStore = pipeline["vector_store"]

    # 检查集合是否已有数据
    try:
        count_info = vector_store.client.count(
            collection_name=vector_store.collection_name,
            exact=True
        )
        if count_info.count > 0:
            print(f"[RAG] 知识库已索引 ({count_info.count} 条)，跳过索引")
            return
    except Exception:
        pass

    # 收集所有支持格式的文档
    supported_exts = (
        "*.txt", "*.md", "*.pdf", "*.csv", "*.html", "*.htm",
        "*.json", "*.xml", "*.yaml", "*.yml",
        "*.py", "*.js", "*.ts", "*.java", "*.c", "*.cpp", "*.h", "*.hpp",
        "*.rs", "*.go", "*.rb", "*.php", "*.swift", "*.kt",
    )
    files = []
    for ext in supported_exts:
        files.extend(glob.glob(os.path.join(knowledge_base_path, "**", ext), recursive=True))
    files = sorted(set(files))

    if not files:
        print(f"[RAG] 知识库路径下未找到支持的文档: {knowledge_base_path}")
        return

    print(f"[RAG] 找到 {len(files)} 个文档，开始索引...")

    chunked_docs = []
    for file_path in files:
        rel_path = os.path.relpath(file_path, knowledge_base_path)
        markdown_text = _convert_to_markdown(file_path)
        if not markdown_text:
            continue

        paragraphs = _split_paragraphs_with_headings(markdown_text)
        chunks = _chunk_paragraphs(paragraphs, chunk_tokens=512, overlap_tokens=32)
        for c in chunks:
            c["source"] = rel_path
        chunked_docs.extend(chunks)

    if not chunked_docs:
        print("[RAG] 未提取到有效文本块")
        return

    print(f"[RAG] 共 {len(chunked_docs)} 个文本块，正在生成向量并存入 Qdrant...")
    for idx, chunk in enumerate(chunked_docs):
        vec = embedding.embed(chunk["content"])
        vector_store.add_vector(
            vector_id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "content": chunk["content"],
                "source": chunk.get("source", ""),
                "heading_path": chunk.get("heading_path"),
                "chunk_index": idx,
            }
        )

    print(f"[RAG] 知识库索引完成，共 {len(chunked_docs)} 个块，来源 {len(files)} 个文档")


def _get_markitdown_instance():
    """
    创建并缓存 MarkItDown 转换器实例（单例模式）
    """
    if not hasattr(_get_markitdown_instance, "_instance"):
        from markitdown import MarkItDown
        _get_markitdown_instance._instance = MarkItDown()
    return _get_markitdown_instance._instance


def _enhanced_pdf_processing(path: str) -> str:
    """
    使用 PyMuPDF 增强 PDF 处理，提取文本并转为 Markdown 格式
    """
    try:
        import fitz
    except ImportError:
        print(f"[RAG] PyMuPDF 未安装，回退到 MarkItDown 处理PDF: {path}")
        md_instance = _get_markitdown_instance()
        if md_instance is None:
            return _fallback_text_reader(path)
        try:
            result = md_instance.convert(path)
            return getattr(result, "text_content", "") or ""
        except Exception:
            return _fallback_text_reader(path)

    try:
        doc = fitz.open(path)
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # 提取标题（字号最大的文本行）
            blocks = page.get_text("dict")["blocks"]
            title = ""
            for block in blocks:
                if block["type"] == 0:  # text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["size"] > 16 and not title:
                                title = span["text"].strip()
                                break

            page_md = f"## 第 {page_num + 1} 页\n\n"
            if title:
                page_md += f"**标题: {title}**\n\n"
            page_md += text.strip() + "\n\n"
            pages.append(page_md)

        doc.close()

        result = "\n".join(pages).strip()
        print(f"[RAG] PyMuPDF 处理成功: {path} -> {len(result)} chars")
        return result
    except Exception as e:
        print(f"[WARNING] PyMuPDF 处理失败 {path}: {e}")
        md_instance = _get_markitdown_instance()
        if md_instance is None:
            return _fallback_text_reader(path)
        try:
            result = md_instance.convert(path)
            return getattr(result, "text_content", "") or ""
        except Exception:
            return _fallback_text_reader(path)


def _fallback_text_reader(path: str) -> str:
    """
    回退方案：以纯文本方式读取文件
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"[RAG] 回退文本读取成功: {path} -> {len(text)} chars")
        return text
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="gbk") as f:
                text = f.read()
            print(f"[RAG] 回退文本读取(GBK)成功: {path} -> {len(text)} chars")
            return text
        except Exception as e:
            print(f"[ERROR] 回退读取失败 {path}: {e}")
            return ""
    except Exception as e:
        print(f"[ERROR] 回退读取失败 {path}: {e}")
        return ""

def _convert_to_markdown(path: str) -> str:
    """
    Universal document reader using MarkItDown with enhanced PDF processing.
    核心功能：将任意格式文档转换为Markdown文本

    支持格式：
    - 文档：PDF、Word、Excel、PowerPoint
    - 图像：JPG、PNG、GIF（通过OCR）
    - 音频：MP3、WAV、M4A（通过转录）
    - 文本：TXT、CSV、JSON、XML、HTML
    - 代码：Python、JavaScript、Java等
    """
    if not os.path.exists(path):
        return ""

    # 对PDF文件使用增强处理
    ext = (os.path.splitext(path)[1] or '').lower()
    if ext == '.pdf':
        return _enhanced_pdf_processing(path)

    # 其他格式使用MarkItDown统一转换
    md_instance = _get_markitdown_instance()
    if md_instance is None:
        return _fallback_text_reader(path)

    try:
        result = md_instance.convert(path)
        markdown_text = getattr(result, "text_content", None)
        if isinstance(markdown_text, str) and markdown_text.strip():
            print(f"[RAG] MarkItDown转换成功: {path} -> {len(markdown_text)} chars Markdown")
            return markdown_text
        return ""
    except Exception as e:
        print(f"[WARNING] MarkItDown转换失败 {path}: {e}")
        return _fallback_text_reader(path)


def _split_paragraphs_with_headings(text: str) -> List[Dict]:
    """
    根据标题层次分割段落，保持语义完整性
    """
    lines = text.splitlines()
    heading_stack: List[str] = []
    paragraphs: List[Dict] = []
    buf: List[str] = []
    char_pos = 0

    def flush_buf(end_pos: int):
        if not buf:
            return
        content = "\n".join(buf).strip()
        if not content:
            return
        paragraphs.append({
            "content": content,
            "heading_path": " > ".join(heading_stack) if heading_stack else None,
            "start": max(0, end_pos - len(content)),
            "end": end_pos,
        })

    for ln in lines:
        raw = ln
        if raw.strip().startswith("#"):
            # 处理标题行
            flush_buf(char_pos)
            level = len(raw) - len(raw.lstrip('#'))
            title = raw.lstrip('#').strip()

            if level <= 0:
                level = 1
            if level <= len(heading_stack):
                heading_stack = heading_stack[:level - 1]
            heading_stack.append(title)

            char_pos += len(raw) + 1
            continue

        # 段落内容累积
        if raw.strip() == "":
            flush_buf(char_pos)
            buf = []
        else:
            buf.append(raw)
        char_pos += len(raw) + 1

    flush_buf(char_pos)

    if not paragraphs:
        paragraphs = [{"content": text, "heading_path": None, "start": 0, "end": len(text)}]

    print("[RAG] 段落分割成功")
    return paragraphs

def _approx_token_len(text: str) -> int:
    """
    近似估计Token长度，支持中英文混合
    """
    # CJK字符按1 token计算
    cjk = sum(1 for ch in text if _is_cjk(ch))
    # 其他字符按空白分词计算
    non_cjk_tokens = len([t for t in text.split() if t])
    return cjk + non_cjk_tokens

def _is_cjk(ch: str) -> bool:
    """
    判断是否为CJK字符
    """
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF or  # CJK统一汉字
        0x3400 <= code <= 0x4DBF or  # CJK扩展A
        0x20000 <= code <= 0x2A6DF or # CJK扩展B
        0x2A700 <= code <= 0x2B73F or # CJK扩展C
        0x2B740 <= code <= 0x2B81F or # CJK扩展D
        0x2B820 <= code <= 0x2CEAF or # CJK扩展E
        0xF900 <= code <= 0xFAFF      # CJK兼容汉字
    )

def _chunk_paragraphs(paragraphs: List[Dict], chunk_tokens: int, overlap_tokens: int) -> List[Dict]:
    """
    基于 Token 数量的智能分块
    """
    chunks: List[Dict] = []
    cur: List[Dict] = []
    cur_tokens = 0
    i = 0

    while i < len(paragraphs):
        p = paragraphs[i]
        p_tokens = _approx_token_len(p["content"]) or 1

        if cur_tokens + p_tokens <= chunk_tokens or not cur:
            cur.append(p)
            cur_tokens += p_tokens
            i += 1
        else:
            content = "\n\n".join(x["content"] for x in cur)
            start = cur[0]["start"]
            end = cur[-1]["end"]
            heading_path = next((x["heading_path"] for x in reversed(cur) if x.get("heading_path")), None)

            chunks.append({
                "content": content,
                "start": start,
                "end": end,
                "heading_path": heading_path,
            })

            # 构建重叠部分
            if overlap_tokens > 0 and cur:
                kept: List[Dict] = []
                kept_tokens = 0
                for x in reversed(cur):
                    t = _approx_token_len(x["content"]) or 1
                    if kept_tokens + t > overlap_tokens:
                        break
                    kept.append(x)
                    kept_tokens += t
                cur = list(reversed(kept))
                cur_tokens = kept_tokens

                # 如果当前段落仍然无法放入 cur（与 overlap 一起），
                # 则清空 overlap 让当前段落作为下一个块起始，防止 i 无法前进的死循环
                if cur and cur_tokens + p_tokens > chunk_tokens:
                    cur = []
                    cur_tokens = 0
            else:
                cur = []
                cur_tokens = 0

    if cur:
        content = "\n\n".join(x["content"] for x in cur)
        start = cur[0]["start"]
        end = cur[-1]["end"]
        heading_path = next((x["heading_path"] for x in reversed(cur) if x.get("heading_path")), None)

        chunks.append({
            "content": content,
            "start": start,
            "end": end,
            "heading_path": heading_path,
        })

    print("[RAG] 智能分块成功")
    return chunks

class RAGTool(Tool):
    """
    RAG 工具
    """

    def __init__(
            self,
            knowledge_base_path: str,
            qdrant_url: str,
            qdrant_api_key: str,
            collection_name: str,
            rag_namespace: str
    ):
        super().__init__(
            name="rag_search",
            description="从本地知识库中检索与问题相关的文本片段，用于辅助回答问题"
        )
        self.knowledge_base_path = knowledge_base_path
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.collection_name = collection_name
        self.rag_namespace = rag_namespace
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        self._indexing_status: Dict[str, str] = {}
        self._indexing_errors: Dict[str, str] = {}
        self._indexing_threads: Dict[str, threading.Thread] = {}
        self._kb_metas: Dict[str, Dict[str, str]] = {}

        default_pipeline = create_rag_pipeline(
            qdrant_url=self.qdrant_url,
            qdrant_api_key=self.qdrant_api_key,
            collection_name=self.collection_name,
            rag_namespace=self.rag_namespace,
            knowledge_base_path=""  # 传空字符串，跳过索引
        )
        self._pipelines[self.rag_namespace] = default_pipeline

    def get_parameters(self) -> List[ToolParameter]:
        kb_hints = []
        for ns, meta in self._kb_metas.items():
            name = meta.get("name", ns)
            desc = meta.get("description", "")
            if desc:
                kb_hints.append(f"  - {ns}: {name} - {desc}")
            else:
                kb_hints.append(f"  - {ns}: {name}")
        if not kb_hints:
            kb_hints.append(f"  - {self.rag_namespace}: 默认知识库")

        namespace_desc = (
            "知识库命名空间，不填则使用默认命名空间。可用知识库:\n"
            + "\n".join(kb_hints)
        )

        return [
            ToolParameter(
                name="query",
                type="string",
                description="检索问题或关键词，用于搜索知识库中相关的内容",
                required=True,
            ),
            ToolParameter(
                name="namespace",
                type="string",
                description=namespace_desc,
                required=False,
                default=self.rag_namespace,
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回的相关文档块数量",
                required=False,
                default=5,
            ),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        检索知识库，返回与查询相关的文本片段
        """
        query = parameters.get("query") or parameters.get("input") or ""
        query = query.strip() if isinstance(query, str) else ""
        if not query:
            return "请提供查询内容"

        namespace = parameters.get("namespace", self.rag_namespace)
        limit = int(parameters.get("limit", 5))

        pipeline = self._pipelines.get(namespace)
        if not pipeline:
            return f"未找到命名空间 '{namespace}' 的 RAG 管道"

        try:
            q_vec = pipeline["embedding"].embed(query)
            results = pipeline["vector_store"].search(
                q_vec,
                limit=limit,
            )

            if not results:
                return "未在知识库中找到相关内容"

            context_parts = []
            for i, r in enumerate(results, 1):
                content = r["payload"].get("content", "")
                source = r["payload"].get("source", "未知来源")
                score = r.get("score", 0)
                context_parts.append(
                    f"[{i}] (相关度: {score:.2f}) [来源: {os.path.basename(source)}]\n{content}"
                )

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            return f"知识库检索失败: {str(e)}"

    def ensure_pipeline(self, namespace: str, collection_name: str) -> bool:
        """
        仅创建管道引用（连接 Qdrant + 加载嵌入模型），不重新索引文件；用于启动恢复，避免与上传线程的索引操作冲突
        """
        if namespace in self._pipelines:
            return True

        try:
            embedding = _RAGEmbedding("all-MiniLM-L6-v2")
            vector_store = _RAGVectorStore(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
                collection_name=collection_name,
                vector_size=embedding.vector_size
            )
            self._pipelines[namespace] = {
                "embedding": embedding,
                "vector_store": vector_store,
                "collection_name": collection_name,
                "namespace": namespace,
            }
            print(f"[RAG] 管道引用已恢复: namespace={namespace}, collection={collection_name}")
            return True
        except Exception as e:
            print(f"[RAG] 恢复管道引用失败 {namespace}: {e}")
            return False

    def _run_indexing_task(
            self,
            namespace: str,
            collection_name: str,
            knowledge_base_path: str
    ):
        """
        后台索引任务函数
        """
        try:
            pipeline = create_rag_pipeline(
                qdrant_url=self.qdrant_url,
                qdrant_api_key=self.qdrant_api_key,
                collection_name=collection_name,
                rag_namespace=namespace,
                knowledge_base_path=knowledge_base_path
            )

            self._pipelines[namespace] = pipeline
            self._indexing_status[namespace] = "done"
            print(f"[RAG] 命名空间 {namespace} 索引任务完成")

        except Exception as e:
            self._indexing_status[namespace] = "failed"
            self._indexing_errors[namespace] = str(e)
            print(f"[RAG] 命名空间 {namespace} 索引任务失败: {e}")

        finally:
            self._indexing_threads.pop(namespace, None)


    def add_pipeline(
            self,
            namespace: str,
            collection_name: str,
            knowledge_base_path: str = "",
            force: bool = False
    ) -> bool:
        """
        动态添加新的 RAG 管道（支持多知识库）
        """
        if namespace in self._pipelines:
            if not force:
                return False
            old = self._pipelines[namespace]
            try:
                old["vector_store"].client.delete_collection(
                    old["vector_store"].collection_name
                )
            except Exception:
                pass
            del self._pipelines[namespace]

        self._indexing_status[namespace] = "indexing"
        self._indexing_errors.pop(namespace, None)

        thread = threading.Thread(
            target=self._run_indexing_task,
            args=(namespace, collection_name, knowledge_base_path or self.knowledge_base_path),
            daemon=True
        )
        thread.start()

        self._indexing_threads[namespace] = thread

        print(f"[RAG] 命名空间 {namespace} 索引任务已启动（后台运行）")
        return True

    def get_index_status(self, namespace: str) -> dict:
        """
        获取命名空间的索引状态
        """
        return {
            "namespace": namespace,
            "status": self._indexing_status.get(namespace, "idle"),
            "error": self._indexing_errors.get(namespace, ""),
            "has_pipeline": namespace in self._pipelines,
        }

    def set_knowledge_bases(self, kb_list: List[Dict[str, Any]]):
        """
        设置所有知识库的元信息（namespace、name、description），用于在工具参数描述中告知 LLM 可用的知识库选项
        """
        self._kb_metas.clear()
        for kb in kb_list:
            ns = kb.get("namespace") or kb.get("ragNamespace") or ""
            if not ns:
                continue
            self._kb_metas[ns] = {
                "name": kb.get("name", ns),
                "description": kb.get("description", ""),
            }
        if self.rag_namespace not in self._kb_metas:
            self._kb_metas[self.rag_namespace] = {
                "name": "默认知识库",
                "description": "",
            }
