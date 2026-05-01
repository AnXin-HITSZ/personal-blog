import json
import os
from typing import List, Optional
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from app.agents.react_agent import ReActAgent
from app.agents.simple_agent import SimpleAgent
from app.core.llm import AgentsLLM
from app.memory.memory_tool import MemoryTool
from app.tools.registry import ToolRegistry
from app.memory.manager import UnifiedMemoryManager
import app.memory.working_memory as working_memory
import app.memory.episodic_memory as episodic_memory

from app.tools.default_tools import CurrentTimeTool


LLM_MODEL_ID = os.getenv('LLM_MODEL_ID')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_BASE_URL = os.getenv('LLM_BASE_URL')
REDIS_URL = os.getenv('REDIS_URL')

llm = AgentsLLM(
    LLM_MODEL_ID,
    LLM_API_KEY,
    LLM_BASE_URL
)

tool_registry = ToolRegistry()
tool_registry.register_tool(CurrentTimeTool())

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

app = FastAPI(title="AI Agent 流式对话服务", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: int

class ChatRequest(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    stream: Optional[bool] = True

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True
    }

memory_tool = MemoryTool(
    memory_manager=memory_manager
)

@app.post("/api/agent/chat/simple_agent/stream")
async def simple_agent_chat_stream(request: ChatRequest):
    if not request.session_id or not request.messages:
        raise HTTPException(400, "参数错误")

    user_input = request.messages[-1].content
    session_id = request.session_id

    relevant_mem = memory_tool.search(
        query=user_input,
        limit=10,
        session_id=session_id
    )

    agent = SimpleAgent(
        LLM_MODEL_ID,
        llm,
        tool_registry,
        relevant_mem
    )

    def generate():
        yield f"data: {json.dumps({'type': 'memory', 'content': relevant_mem}, ensure_ascii=False)}\n\n"
        full_resp = ""
        for chunk in agent.run(user_input, max_tool_iterations=3, stream=request.stream):
            full_resp += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

        # wm.add_message(session_id, "user", user_input, 0.8)
        # wm.add_message(session_id, "assistant", full_resp, 0.7)
        memory_tool.add_memory(session_id, "user", user_input, 0.8)
        memory_tool.add_memory(session_id, "assistant", full_resp, 0.7)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

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

    agent = ReActAgent(
        LLM_MODEL_ID,
        llm,
        tool_registry,
        5,
        relevant_mem
    )

    def generate():
        yield f"data: {json.dumps({'type': 'memory', 'content': relevant_mem}, ensure_ascii=False)}\n\n"

        final_resp = ""
        for event in agent.run(user_input, stream=True):
            event_type = event["type"]
            event_data = event["data"]

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if event_type == "final_answer":
                final_resp = event_data

        if final_resp:
            # wm.add_message(session_id, "user", user_input, 0.8)
            # wm.add_message(session_id, "assistant", final_resp, 0.7)
            memory_tool.add_memory(session_id, "user", user_input, 0.8)
            memory_tool.add_memory(session_id, "assistant", final_resp, 0.7)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
