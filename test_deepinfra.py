import urllib.request
import json

# Test DeepInfra
req = urllib.request.Request(
    "http://127.0.0.1:8000/chat/generate",
    data=json.dumps({"messages": [{"role": "user", "content": "count to 3"}]}).encode(
        "utf-8"
    ),
    headers={
        "Content-Type": "application/json",
        "X-Provider": "deepinfra-free",
        "X-Model": "meta-llama/Meta-Llama-3-8B-Instruct",
    },
)
try:
    resp = urllib.request.urlopen(req)
    with open("response_deepinfra.txt", "w", encoding="utf-8") as f:
        f.write(resp.read().decode("utf-8"))
    print("DeepInfra response saved")
except urllib.error.HTTPError as e:
    with open("response_deepinfra.txt", "w", encoding="utf-8") as f:
        f.write(f"Error {e.code}: {e.read().decode('utf-8')}")
    print(f"Error: {e.code}")
