import csv
import io
from .models import STATUS_LABELS


def safe_cell(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


def export_csv(task, approved_only):
    if approved_only and task["status"] != "reviewed":
        raise ValueError("请先完成审核，再导出已批准答复")
    items = [i for i in task["items"] if not approved_only or i["reviewer_action"] == "approve"]
    if not items:
        raise ValueError("没有可导出的已批准答复")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["客户（模拟）", "需求原文", "能力结论", "客户答复", "依据编号", "审核状态", "版本", "部署"])
    for item in items:
        writer.writerow([safe_cell(v) for v in [task["customer"], item["requirement"]["text"],
            STATUS_LABELS[item["status"]], item["reviewed_answer"] or item["answer"],
            ";".join(c["doc_id"] for c in item["citations"]),
            "已批准" if item["reviewer_action"] == "approve" else "草稿 / 退回",
            task["version"], task["deployment"]]])
    return stream.getvalue().encode("utf-8-sig")


def import_csv(data):
    if len(data) > 200000:
        raise ValueError("CSV 最大 200 KB")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("请使用 UTF-8 编码的 CSV") from None
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "requirement" not in reader.fieldnames:
        raise ValueError("CSV 必须包含 requirement 列")
    if len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("CSV 列名不能重复")
    rows = list(reader)
    if any(row.get("requirement") is None or None in row for row in rows):
        raise ValueError("CSV 行的单元格数量与表头不一致，请补齐 requirement 单元格")
    lines = [row["requirement"].strip() for row in rows]
    lines = [line for line in lines if line]
    if not lines or len(lines) > 40 or any("\n" in line for line in lines):
        raise ValueError("CSV 须包含 1–40 行非空需求，每个单元格一项")
    return "\n".join(lines)
