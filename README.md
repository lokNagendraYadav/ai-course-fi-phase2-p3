# LangChain Dev Chat

A local AI development environment with a split-panel web UI — chat with an LLM on the left, watch every LangChain operation trace live on the right.

## Stack

| Layer | Tool |
|---|---|
| LLM | Gemini 3.1 Flash Lite via [Google AI Studio](https://aistudio.google.com/apikey) |
| Framework | [LangChain](https://python.langchain.com) |
| Observability | [LangSmith](https://smith.langchain.com) |
| Backend | FastAPI + uvicorn |
| Frontend | Vanilla HTML/CSS/JS (no build step) |

## Project structure

```
my-langchain-app/
├── server.py      # FastAPI server — serves UI and streams LangChain events
├── index.html     # Split-panel chat + live trace UI
├── main.py        # Standalone chain script (original)
├── .env           # API keys (never commit this)
└── venv/          # Python virtual environment
```

## Setup

### 1. Clone and enter the directory

```bash
cd my-langchain-app
```

### 2. Create and activate the virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install langchain langchain-google-genai langchain-core langsmith fastapi uvicorn python-dotenv
```

### 4. Configure environment variables

Create a `.env` file (copy the template below):

```env
GEMINI_API_KEY=your_gemini_api_key
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=my-langchain-app
```

- Get a Gemini key → https://aistudio.google.com/apikey
- Get a LangSmith key → https://smith.langchain.com

## Running

### Web UI (chat + live trace)

```bash
python server.py
```

Open **http://localhost:8000** in your browser.

The UI shows:
- **Left panel** — chat interface with streaming responses
- **Right panel** — live LangChain execution trace (pipeline steps, token counts, timing)

### Standalone script

```bash
python main.py
```

Runs a single hardcoded question through the chain and prints the response to the terminal.

## How it works

The chain is a simple LangChain pipeline:

```
ChatPromptTemplate  →  ChatGoogleGenerativeAI (Gemini 3.1 Flash Lite)  →  StrOutputParser
```

`server.py` uses `astream_events` (LangChain v2) to stream every internal event — prompt formatting, LLM call, token chunks, parser output — as Server-Sent Events to the browser in real time.

LangSmith tracing is enabled automatically via the `LANGCHAIN_TRACING_V2=true` env var. Each run is logged to your LangSmith project dashboard.
