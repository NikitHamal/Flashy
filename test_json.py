import subprocess
import json
import os

env = os.environ.copy()
env["FLASHY_API_URL"] = "http://127.0.0.1:8000"

process = subprocess.Popen(
    [
        "node",
        "F:\\Flashy\\qwen-code\\dist\\cli.js",
        "--auth-type",
        "qwen-free",
        "--model",
        "qwen3.6-plus",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    env=env,
)

print("Writing initialization control request...")
msg = {"type": "submit_prompt", "prompt": [{"type": "text", "text": "hi"}]}
process.stdin.write(json.dumps(msg) + "\n")
process.stdin.flush()

for i in range(15):
    line = process.stdout.readline()
    if not line:
        break
    print(line.strip())

process.terminate()
