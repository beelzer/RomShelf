#!/usr/bin/env python3
"""Launch script for ROM Shelf."""

import sys
from pathlib import Path

# Add src to path so we can import rom_shelf
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rom_shelf.main import main

if __name__ == "__main__":
    sys.exit(main())
