import os
import sys
import subprocess


def _run(module_name: str):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    subprocess.run([sys.executable, "-m", module_name], env=env)


def run():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "flashy").lower()
    target = {
        "flashy": "backend.app",
        "server": "backend.server_app",
        "duckai": "backend.duckai_control",
    }.get(mode)

    if not target:
        raise SystemExit("Usage: python run.py [flashy|server|duckai]")

    if mode == "duckai":
        from backend.duckai_control import start, stop
        import atexit
        atexit.register(stop)
        result = start()
        print(f"DuckAI status: {result}")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    print(f"Starting {mode}...")
    try:
        _run(target)
    except KeyboardInterrupt:
        print(f"\nStopping {mode}...")


if __name__ == "__main__":
    run()
