"""只运行离线合成开发案例，保存每次完整输出，不调用付费模型。"""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from presales.analyzer import Analyzer
from presales.catalog import Catalog


def main():
    raw = (ROOT / "fixtures/evaluation_cases.json").read_bytes()
    cases = json.loads(raw)["cases"]
    catalog = Catalog.load(ROOT / "fixtures/catalog.json")
    engine = Analyzer(catalog)
    results = []
    for case in cases:
        started = time.perf_counter()
        try:
            items = engine.analyze(case["text"], case["deployment"], case["role"], "3.2", "demo")
            actual = [i.status for i in items]
            results.append({**case, "actual": actual, "passed": actual == case["expected"],
                "seconds": round(time.perf_counter() - started, 6),
                "items": [i.model_dump() for i in items], "error": None})
        except Exception as exc:
            results.append({**case, "actual": [], "passed": False, "seconds": round(time.perf_counter() - started, 6),
                            "items": [], "error": f"{type(exc).__name__}: {exc}"})
    stamp = datetime.now(timezone.utc)
    result = dict(generated_at=stamp.isoformat(), mode="demo", synthetic=True, model_calls=0,
        total=len(cases), passed=sum(r["passed"] for r in results),
        catalog_hash=catalog.fingerprint, cases_hash=hashlib.sha256(raw).hexdigest(),
        cases=results, limitations="规则回归案例，未进行真实模型评测或真实用户效率验证；不代表语义泛化能力。")
    folder = ROOT / "evaluation"
    folder.mkdir(exist_ok=True)
    destination = folder / f"{stamp.strftime('%Y%m%dT%H%M%S%fZ')}_demo.json"
    content = json.dumps(result, ensure_ascii=False, indent=2)
    destination.write_text(content, encoding="utf-8")
    (folder / "latest.json").write_text(content, encoding="utf-8")
    print(f"合成开发案例：{result['passed']}/{result['total']}；模型调用：0；完整输出：{destination}")
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
