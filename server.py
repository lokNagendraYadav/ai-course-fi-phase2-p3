import json
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
])
llm = ChatGroq(model="llama-3.1-8b-instant")
chain = prompt_template | llm | StrOutputParser()


@app.get("/")
async def frontend():
    return HTMLResponse(Path("index.html").read_text(encoding="utf-8"))


class ChatRequest(BaseModel):
    message: str


def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def log_event(level: str, title: str, event: str = "", detail: str = "", **extra) -> dict:
    return {"type": "log", "level": level, "event": event, "title": title, "detail": detail, **extra}


@app.post("/chat")
async def chat(req: ChatRequest):
    async def stream():
        try:
            async for ev in chain.astream_events({"question": req.message}, version="v2"):
                kind = ev["event"]
                name = ev.get("name", "")
                data = ev.get("data", {})
                payload = None

                if kind == "on_chain_start":
                    if name == "RunnableSequence":
                        q = req.message
                        preview = q[:80] + ("..." if len(q) > 80 else "")
                        payload = log_event("chain", "Pipeline started", kind, f'Input: "{preview}"')
                    elif name == "ChatPromptTemplate":
                        payload = log_event("prompt", "Formatting prompt", kind,
                                            "Applying system + user message template")
                    elif "Parser" in name or "parser" in name.lower():
                        payload = log_event("parser", "Parsing output", kind, name)

                elif kind == "on_chain_end":
                    if name == "RunnableSequence":
                        payload = log_event("chain", "Pipeline complete", kind, "All steps finished")
                    elif name == "ChatPromptTemplate":
                        out = data.get("output")
                        detail = "Messages formatted"
                        if out and hasattr(out, "messages"):
                            parts = []
                            for m in out.messages:
                                role = type(m).__name__.replace("Message", "").lower()
                                snippet = m.content[:55] + ("..." if len(m.content) > 55 else "")
                                parts.append(f'{role}: "{snippet}"')
                            detail = "  ·  ".join(parts)
                        payload = log_event("prompt", "Prompt ready", kind, detail)
                    elif "Parser" in name or "parser" in name.lower():
                        payload = log_event("parser", "Output parsed", kind, "String extraction complete")

                elif kind == "on_chat_model_start":
                    inp = data.get("input", {})
                    msg_count = sum(len(m) for m in inp.get("messages", []))
                    payload = log_event("llm", f"LLM request → {name}", kind,
                                        f"llama-3.1-8b-instant via Groq  ·  {msg_count} message(s)")

                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload = {"type": "token", "content": chunk.content}

                elif kind == "on_chat_model_end":
                    out = data.get("output")
                    tokens = {}
                    if out and hasattr(out, "usage_metadata") and out.usage_metadata:
                        um = out.usage_metadata
                        tokens = {
                            "input": um.get("input_tokens", 0),
                            "output": um.get("output_tokens", 0),
                            "total": um.get("total_tokens", 0),
                        }
                    detail = "Response generated"
                    if tokens:
                        detail = (f"Input: {tokens['input']} tok  ·  "
                                  f"Output: {tokens['output']} tok  ·  "
                                  f"Total: {tokens['total']} tok")
                    payload = log_event("llm", "LLM response complete", kind, detail, tokens=tokens)

                if payload:
                    yield sse(payload)

            yield sse({"type": "done"})

        except Exception as e:
            yield sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
