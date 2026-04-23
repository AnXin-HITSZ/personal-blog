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
from app.tools.registry import ToolRegistry
from app.core.redis import RedisChatService
from app.core.message import Message

from app.tools.default_tools import CurrentTimeTool

LLM_MODEL_ID = os.getenv('LLM_MODEL_ID')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_BASE_URL = os.getenv('LLM_BASE_URL')

llm = AgentsLLM(
    LLM_MODEL_ID,
    LLM_API_KEY,
    LLM_BASE_URL
)

tool_registry = ToolRegistry()
tool_registry.register_tool(CurrentTimeTool())

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

class ChatRequest(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    stream: Optional[bool] = True

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True
    }

@app.post("/api/agent/chat/simple_agent/stream")
async def simple_agent_chat_stream(request: ChatRequest):
    if not request.session_id or not request.messages:
        raise HTTPException(400, "参数错误")

    user_input = request.messages[-1].content
    session_id = request.session_id

    history = RedisChatService.get_chat_history(session_id)

    agent = SimpleAgent(
        LLM_MODEL_ID,
        llm,
        tool_registry
    )

    for msg in history:
        agent.add_message(Message(**msg))

    def generate():
        full_resp = ""
        for chunk in agent.run(user_input, max_tool_iterations=3, stream=request.stream):
            full_resp += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

        new_history = history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": full_resp}
        ]
        RedisChatService.save_chat_history(session_id, new_history)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/agent/react_agent/chat/stream")
async def react_agent_chat_stream(request: ChatRequest):
    if not request.session_id or not request.messages:
        raise HTTPException(400, "参数错误")

    user_input = request.messages[-1].content
    session_id = request.session_id

    history = RedisChatService.get_chat_history(session_id)

    agent = ReActAgent(
        LLM_MODEL_ID,
        llm,
        tool_registry
    )

    for msg in history:
        agent.add_message(Message(**msg))

    def generate():
        final_resp = ""
        for event in agent.run(user_input, stream=True):
            event_type = event["type"]
            event_data = event["data"]

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if event_type == "final_answer":
                final_resp = event_data

        if final_resp:
            new_history = history + [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": final_resp}
            ]
            RedisChatService.save_chat_history(session_id, new_history)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
