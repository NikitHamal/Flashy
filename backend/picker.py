import tkinter as tk
from tkinter import filedialog
import os
import sys

def pick_folder():
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askdirectory()
        root.destroy()
        if path:
            print(os.path.abspath(path))
        else:
            print("CANCELLED")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    pick_folder()
