# backend/tests/__init__.py
import sys
from pathlib import Path

# Ensure the backend package root is on sys.path so tests can import modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
