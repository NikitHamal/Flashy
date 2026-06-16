import subprocess, json, os, base64

BUN_PATH = os.path.expanduser(r"~\AppData\Roaming\npm\node_modules\bun\bin\bun.exe")
VQD_SCRIPT = os.path.join(os.path.dirname(__file__), "compute_vqd.js")

def compute_vqd(base64_hash: str, user_agent: str = "") -> str:
    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    input_data = json.dumps({"base64Hash": base64_hash, "userAgent": user_agent})
    env = os.environ.copy()
    env["NODE_PATH"] = os.path.join(os.path.dirname(__file__), "..", "..", "duckai", "node_modules")
    result = subprocess.run(
        [BUN_PATH, "run", VQD_SCRIPT],
        input=input_data,
        capture_output=True, text=True, timeout=45, env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"VQD compute failed: {result.stderr[:200]}")
    return result.stdout.strip()
