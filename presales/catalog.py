import hashlib
import json
from pathlib import Path
from .models import Source


class Catalog:
    def __init__(self, records):
        self.records = [Source.model_validate(r) for r in records]
        self.by_id = {r.id: r for r in self.records}
        if len(self.by_id) != len(self.records):
            raise ValueError("资料 ID 重复")
        self.aliases = {}
        for record in self.records:
            self.aliases.setdefault(record.capability, set()).update(record.aliases)
        self.fingerprint = hashlib.sha256(json.dumps(
            [r.model_dump() for r in self.records], ensure_ascii=False,
            sort_keys=True).encode()).hexdigest()

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8"))["documents"])

    def visible(self, role):
        if role not in ("sales", "reviewer"):
            raise ValueError("未知资料角色")
        return [r for r in self.records if r.access == "sales" or role == "reviewer"]
