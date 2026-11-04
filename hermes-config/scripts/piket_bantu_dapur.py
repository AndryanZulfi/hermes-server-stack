#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from piket_reminder import run_reminder

if __name__ == "__main__":
    run_reminder("dapur")
