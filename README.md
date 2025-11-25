## FastAPI RAG Service

This folder hosts a lightweight FastAPI layer that accepts a user query, automatically calls the vector-store RAG service to obtain the top-k documents, and then forwards a grounded prompt to SiliconFlow's chat completion API.

### 1. Environment Setup

```bash
cd RecipeProjectService
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials & Endpoints

All service knobs live in `app/config.py`. Edit the constants near the top of that file to set:

- `DEFAULT_SILICONFLOW_API_KEY`: the key issued by SiliconFlow (required).
- `DEFAULT_SILICONFLOW_BASE_URL` and timeout.
- Retrieval endpoint (`DEFAULT_RAG_URL`), top-k, and rerank behaviour.
- Model hyper-parameters (temperature, top_p, max_tokens, etc.).

No environment variables are read at runtime, so checking the file into source control keeps configuration transparent.

- Edit the system/user prompt template in `app/prompt.py` when you need to adjust instructions.

### 3. Run the API Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://127.0.0.1:8000/` for the built-in playground UI (Ctrl/Cmd+Enter sends, “流式输出” 开关可即时查看 streaming token)，或 `http://127.0.0.1:8000/docs` 查看 Swagger。

### 4. Request/Response Example

`POST /chat`

```json
{
  "query": "How can I adapt this curry recipe for vegans?",
  "top_k": 5,
  "stream": false,
  "use_rerank": true,
  "rerank_mode": "cross",
  "rerank_top_k": 5
}
```

`use_rerank`, `rerank_mode` (cross/bi) 与 `rerank_top_k` 均为可选字段；不传时跟随 `app/config.py` 中的默认配置。UI 中的“重排策略/模式/Top-K”下拉框可实时测试这些参数。

Sample success payload (non-streaming):

```json
{
  "answer": "You can replace the ghee with neutral oil and rely on coconut milk (doc-1) ...",
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "usage": {
    "prompt_tokens": 345,
    "completion_tokens": 128,
    "total_tokens": 473
  },
  "documents": [
    {"id": "doc-1", "title": "Chickpea Curry", "content": "Use coconut milk...", "score": 0.88},
    {"id": "doc-2", "title": null, "content": "Swap ghee with oil", "score": 0.86}
  ],
  "raw_response": {"id": "...", "choices": [...], "usage": {...}}
}
```

When `"stream": true`, the endpoint returns Server-Sent Events (`text/event-stream`). Events include:

- `meta`: model name + retrieved documents.
- `delta`: incremental text tokens.
- `end`: final answer summary.
- `error`: reason when upstream fails.

### 5. Direct SiliconFlow Call (Reference)

If you need to call the upstream API manually, the service mirrors SiliconFlow's `chat/completions` endpoint:

```python
import requests

url = "https://api.siliconflow.cn/v1/chat/completions"
payload = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Example question"}]
}
headers = {
    "Authorization": "Bearer sk-REPLACE_ME",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, timeout=30)
print(response.json())
```
