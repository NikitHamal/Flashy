import urllib.request
import json

req = urllib.request.Request(
    "http://127.0.0.1:8000/chat/generate",
    data=json.dumps({"messages": [{"role": "user", "content": "hi"}]}).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "X-Provider": "qwen-free",
        "X-Model": "qwen3.6-plus",
    },
)
try:
    resp = urllib.request.urlopen(req)
    with open("response.txt", "w", encoding="utf-8") as f:
        f.write(resp.read().decode("utf-8"))
    print("Response saved to response.txt")
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print(e.read().decode("utf-8"))
