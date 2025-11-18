## For Python Usage

API_KEY:

```
API_KEY = "sk-wjrtizmtakyahakiovtuqynxrvzaafpcbrxddfdlutaglfhj"
```

Avalible Models:
```
Qwen/Qwen2.5-7B-Instruct
Qwen/Qwen3-8B
THUDM/GLM-4.1V-9B-Thinking
THUDM/glm-4-9b-chat
```

Example for Python code:

```python
import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
        }
    ]
}
headers = {
    "Authorization": "Bearer sk-wjrtizmtakyahakiovtuqynxrvzaafpcbrxddfdlutaglfhj",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

Expected Response:

status code <200>
```
{
  "id": "<string>",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<string>",
        "reasoning_content": "<string>",
        "tool_calls": [
          {
            "id": "<string>",
            "type": "function",
            "function": {
              "name": "<string>",
              "arguments": "<string>"
            }
          }
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 123,
    "total_tokens": 123
  },
  "created": 123,
  "model": "<string>",
  "object": "chat.completion"
}
```
