import asyncio
import sys
from pathlib import Path

# Repo root on sys.path so `python example/main.py` works without `pip install -e .`
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from nitrado import Global


async def main() -> None:
    health = await Global.version()
    print(health.status)
    print(health.message)


if __name__ == "__main__":
    asyncio.run(main())
