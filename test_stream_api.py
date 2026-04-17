import urllib.request
import json

req = urllib.request.Request(
    "http://127.0.0.1:8000/chat/generate/stream",
    data=json.dumps({"messages": [{"role": "user", "content": "count to 3"}]}).encode(
        "utf-8"
    ),
    headers={
        "Content-Type": "application/json",
        "X-Provider": "qwen-free",
        "X-Model": "qwen3.6-plus",
    },
)
try:
    resp = urllib.request.urlopen(req)
    with open("response_stream.txt", "w", encoding="utf-8") as f:
        while True:
            chunk = resp.read(1024)
            if not chunk:
                break
            f.write(chunk.decode("utf-8"))
    print("Streaming response saved to response_stream.txt")
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print(e.read().decode("utf-8"))
