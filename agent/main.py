import json
import os
import shutil
import threading
import urllib.request
import urllib.error
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from app.agents.react_agent import ReActAgent
from app.agents.simple_agent import SimpleAgent
from app.core.llm import AgentsLLM
from app.core.message import Message
from app.core.redis import RedisChatService
from app.memory.memory_tool import MemoryTool
from app.tools.registry import ToolRegistry
from app.memory.manager import UnifiedMemoryManager
import app.memory.working_memory as working_memory
import app.memory.episodic_memory as episodic_memory

from app.tools.default_tools import CurrentTimeTool, WriteBlogTool
from app.tools.default_tools.rag_tool import RAGTool


LLM_MODEL_ID = os.getenv('LLM_MODEL_ID')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_BASE_URL = os.getenv('LLM_BASE_URL')
REDIS_URL = os.getenv('REDIS_URL')
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
KNOWLEDGE_BASE_PATH = os.getenv('KNOWLEDGE_BASE_PATH', './knowledge_base')
BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', 'http://localhost:8080')

llm = AgentsLLM(
    LLM_MODEL_ID,
    LLM_API_KEY,
    LLM_BASE_URL
)

tool_registry = ToolRegistry()
tool_registry.register_tool(CurrentTimeTool())
rag_tool = RAGTool(
    knowledge_base_path=KNOWLEDGE_BASE_PATH,
    qdrant_url=QDRANT_URL,
    qdrant_api_key="",
    collection_name="rag_knowledge_base",
    rag_namespace="default"
)
tool_registry.register_tool(rag_tool)
tool_registry.register_tool(WriteBlogTool())

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动时恢复知识库管道，关闭时清理资源
    """
    # startup
    threading.Thread(target=_rebuild_pipelines_on_startup, daemon=True).start()
    yield
    # shutdown（暂不需要清理操作）

memory_manager = UnifiedMemoryManager(
    working_memory_config=working_memory.MemoryConfig(
        redis_url=REDIS_URL,
        memory_capacity=50,
        ttl_seconds=120,
        default_importance=0.5
    ),
    episodic_memory_config=episodic_memory.MemoryConfig(
        database_path="./episodic_memory.db",
        qdrant_url="http://localhost:6333",
        qdrant_api_key="",
        qdrant_collection_name="episodic_memory",
        embedding_model_name="all-MiniLM-L6-v2",
        memory_capacity=1000,
        vector_weight=0.6,
        keyword_weight=0.4,
        time_decay_half_life_days=7.0
    )
)

app = FastAPI(title="AI Agent 流式对话服务", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _rebuild_pipelines_on_startup():
    """
    启动时从 MySQL 恢复所有知识库管道
    """
    try:
        req = urllib.request.Request(f"{BACKEND_BASE_URL}/api/rag/list")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
        kbs = body.get("data", []) if isinstance(body, dict) else body
    except Exception as e:
        print(f"[启动] 从后端加载知识库列表失败: {e}")
        kbs = []

    rag_tool.set_knowledge_bases(kbs)

    for kb in kbs:
        namespace = kb.get("namespace")
        collection_name = kb.get("collectionName") or f"rag_{namespace}"
        file_path = kb.get("filePath", "")
        if not namespace or namespace == "default":
            continue

        try:
            rag_tool.ensure_pipeline(
                namespace=namespace,
                collection_name=collection_name
            )
            print(f"[启动] 恢复知识库管道: {kb.get('name')} ({namespace})")
        except Exception as e:
            print(f"[启动] 恢复知识库管道失败: {namespace} → {e}")


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: int

class ChatRequest(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    stream: Optional[bool] = True
    user_id: Optional[int] = None

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True
    }

memory_tool = MemoryTool(
    memory_manager=memory_manager
)

@app.post("/api/agent/rag/upload")
async def rag_upload(
    namespace: str = Form(...),
    collection_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    接收前端上传的知识库文件，保存到固定路径并在后台触发 RAG 索引
    """
    if not namespace or not collection_name or not files:
        raise HTTPException(400, "参数错误")

    kb_dir = os.path.join(rag_tool.knowledge_base_path, namespace)
    os.makedirs(kb_dir, exist_ok=True)

    saved = []
    for file in files:
        if not file.filename:
            continue
        file_path = os.path.join(kb_dir, file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        saved.append(file.filename)

    if not saved:
        raise HTTPException(400, "没有有效的文件")

    rag_tool._indexing_status[namespace] = "indexing"
    rag_tool._indexing_errors.pop(namespace, None)

    def _index_task():
        try:
            rag_tool.add_pipeline(
                namespace=namespace,
                collection_name=collection_name,
                knowledge_base_path=kb_dir,
                force=True
            )
            print(f"[RAG] 后台索引完成: namespace={namespace}")
        except Exception as e:
            print(f"[RAG] 后台索引失败: {e}")

    threading.Thread(target=_index_task, daemon=True).start()

    return {
        "success": True,
        "message": f"已上传 {len(saved)} 个文件，后台索引中",
        "fileCount": len(saved)
    }

@app.get("/api/agent/rag/index_status/{namespace}")
async def rag_index_status(namespace: str):
    """
    查询指定命名空间的索引状态
    """
    status = rag_tool.get_index_status(namespace)
    return status

# @app.post("/api/agent/chat/simple_agent/stream")
# async def simple_agent_chat_stream(request: ChatRequest):
#     if not request.session_id or not request.messages:
#         raise HTTPException(400, "参数错误")
#
#     user_input = request.messages[-1].content
#     session_id = request.session_id
#
#     relevant_mem = memory_tool.search(
#         query=user_input,
#         limit=10,
#         session_id=session_id
#     )
#
#     history_messages = RedisChatService.get_chat_history(session_id)
#
#     agent = SimpleAgent(
#         LLM_MODEL_ID,
#         llm,
#         tool_registry,
#         relevant_mem
#     )
#     for msg in history_messages:
#         agent.add_message(Message(content=msg["content"], role=msg["role"]))
#
#     def generate():
#         yield f"data: {json.dumps({'type': 'memory', 'content': relevant_mem}, ensure_ascii=False)}\n\n"
#         full_resp = ""
#         for chunk in agent.run(user_input, max_tool_iterations=3, stream=request.stream):
#             full_resp += chunk
#             yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
#
#         memory_tool.add_memory(session_id, "user", user_input, 0.8)
#         memory_tool.add_memory(session_id, "assistant", full_resp, 0.7)
#         history_messages.append({"role": "user", "content": user_input})
#         history_messages.append({"role": "assistant", "content": full_resp})
#         RedisChatService.save_chat_history(session_id, history_messages)
#         yield "data: [DONE]\n\n"
#
#     return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/agent/chat/react_agent/stream")
async def react_agent_chat_stream(request: ChatRequest):
    if not request.session_id or not request.messages:
        raise HTTPException(400, "参数错误")

    user_input = request.messages[-1].content
    session_id = request.session_id

    relevant_mem = memory_tool.search(
        query=user_input,
        limit=10,
        session_id=session_id
    )

    history_messages = RedisChatService.get_chat_history(session_id)

    agent = ReActAgent(
        LLM_MODEL_ID,
        llm,
        tool_registry,
        5,
        relevant_mem,
        user_id=request.user_id
    )
    for msg in history_messages:
        agent.add_message(Message(content=msg["content"], role=msg["role"]))

    def generate():
        yield f"data: {json.dumps({'type': 'memory', 'content': relevant_mem}, ensure_ascii=False)}\n\n"

        final_resp = ""
        full_resp = ""
        for event in agent.run(user_input, stream=True):
            event_type = event["type"]
            event_data = event["data"]

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if event_type == "final_answer":
                final_resp = event_data
                full_resp = event.get("full_response", event_data)

        if final_resp:
            memory_tool.add_memory(session_id, "user", user_input, 0.8)
            memory_tool.add_memory(session_id, "assistant", final_resp, 0.7)
            history_messages.append({"role": "user", "content": user_input})
            history_messages.append({"role": "assistant", "content": full_resp or final_resp})
            RedisChatService.save_chat_history(session_id, history_messages)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
