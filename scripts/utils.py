\
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def read_env():
    # Load .env if present; Jenkins can still override via real env
    load_dotenv()

def get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    v = os.getenv(name, default)
    if required and not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def bump_version(version_file: str) -> int:
    vf = Path(version_file)
    if vf.exists():
        try:
            cur = int(vf.read_text(encoding="utf-8").strip())
        except Exception:
            cur = 0
    else:
        ensure_dir(vf.parent.as_posix())
        cur = 0
    new_v = cur + 1
    vf.write_text(str(new_v), encoding="utf-8")
    return new_v
