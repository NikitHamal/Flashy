import os
import sys
import subprocess

def run():
    print("Starting Flashy...")
    # Add the current directory to sys.path so backend can be imported
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    try:
        subprocess.run([sys.executable, "-m", "backend.app"], env=env)
    except KeyboardInterrupt:
        print("\nStopping Flashy...")

if __name__ == "__main__":
    run()
