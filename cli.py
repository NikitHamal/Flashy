#!/usr/bin/env python3
"""Compatibility shim for the production Flashy CLI package."""
from __future__ import annotations

from flashy_cli import __version__, main

if __name__ == "__main__":
    main()
