from setuptools import setup, find_packages

setup(
    name="flashy",
    version="0.2.0",
    description="Flashy - minimal, fast AI coding assistant CLI and local workspace agent",
    py_modules=["cli"],
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "python-multipart>=0.0.9",
        "pydantic>=2.5.3",
        "aiohttp>=3.13.4",
        "httpx>=0.27.0",
        "beautifulsoup4>=4.12.0",
        "rich>=13.0.0",
        "questionary>=2.0.0",
        "prompt_toolkit>=3.0.0",
        "chardet>=5.2.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "flashy=flashy_cli:main",
            "flashy-cli=flashy_cli:main",
        ],
    },
)
