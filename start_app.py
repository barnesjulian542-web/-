import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="启动有据售前工作台，默认端口8504")
    parser.add_argument("--port", type=int, default=8504)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("端口须为1024–65535")
    environment = os.environ.copy()
    environment["NO_PROXY"] = ",".join(filter(None, [environment.get("NO_PROXY", ""), "127.0.0.1", "localhost"]))
    environment["PYTHONUTF8"] = "1"
    print(f"有据工作台：http://127.0.0.1:{args.port}", flush=True)
    try:
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
            "--server.port", str(args.port), "--server.address", "127.0.0.1", "--server.headless", "true"],
            cwd=ROOT, env=environment)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
