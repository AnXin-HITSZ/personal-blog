import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from starlette.responses import StreamingResponse

from app.core.llm import AgentsLLM

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    llm_client = AgentsLLM()
except Exception as e:
    print(f"LLM 初始化失败: {e}")
    llm_client = None

class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user"])
    content: str = Field(..., examples=["你好！"])

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    is_stream: Optional[bool] = True

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None

@app.post("/api/agent/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    供 SpringBoot 调用的流式聊天接口
    """

    if not llm_client:
        raise HTTPException(status_code=500, detail="AI 服务未初始化")

    messages = [msg.model_dump() for msg in request.messages]

    def generate():
        for chunk in llm_client.stream_invoke(messages, temperature=request.temperature):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
