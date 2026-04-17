import requests
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Test non-streaming
r = requests.post(
    "http://127.0.0.1:8000/chat/generate",
    json={"messages": [{"role": "user", "content": "hello"}]},
    headers={"X-Provider": "qwen-free", "X-Model": "qwen3.5-plus"},
)
print("Non-streaming response:", r.text[:500])

# Test streaming
r = requests.post(
    "http://127.0.0.1:8000/chat/generate/stream",
    json={"messages": [{"role": "user", "content": "count 1 to 2"}]},
    headers={"X-Provider": "qwen-free", "X-Model": "qwen3.5-plus"},
    stream=True,
)
print("\n\nStreaming response:")
for line in r.iter_lines():
    if line:
        print(line.decode("utf-8"))
