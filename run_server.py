import os
import sys
import subprocess


def run():
    print("Starting Flashy provider server...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    try:
        subprocess.run([sys.executable, "-m", "backend.server_app"], env=env)
    except KeyboardInterrupt:
        print("\nStopping Flashy provider server...")


if __name__ == "__main__":
    run()
