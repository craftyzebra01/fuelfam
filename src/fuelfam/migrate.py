import sys
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def main() -> None:
    args = sys.argv[1:]
    if not args[0]:
        sys.exit(1)

    conn = sqlite3.connect(args[0])

    try:
        current = conn.execute("PRAGMA user_version").
