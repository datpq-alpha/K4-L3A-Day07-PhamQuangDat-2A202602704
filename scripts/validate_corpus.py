#!/usr/bin/env python3
"""Validate corpus files, frontmatter, sources.csv, and audience coverage."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


REQUIRED_FIELDS = (
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
)
ALLOWED_AUDIENCES = {"student", "faculty", "staff", "all"}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---(?:\s*\n|$)", text, flags=re.DOTALL)
    if not match:
        return {}

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kiểm tra corpus trước benchmark.")
    parser.add_argument(
        "corpus_dir",
        nargs="?",
        type=Path,
        default=Path("data/academic_regulations"),
        help="Thư mục chứa các file .md và sources.csv",
    )
    return parser.parse_args()


def main() -> int:
    corpus_dir = parse_args().corpus_dir
    manifest_path = corpus_dir / "sources.csv"
    failures: list[str] = []

    if not corpus_dir.is_dir():
        print(f"THẤT BẠI: không tìm thấy thư mục {corpus_dir}")
        return 1
    if not manifest_path.is_file():
        print(f"THẤT BẠI: không tìm thấy {manifest_path}")
        return 1

    markdown_files = sorted(corpus_dir.glob("*.md"))
    document_ids: list[str] = []
    audiences: Counter[str] = Counter()

    for path in markdown_files:
        metadata = parse_frontmatter(path)
        missing = [field for field in REQUIRED_FIELDS if not metadata.get(field)]
        doc_id = metadata.get("doc_id", "")
        audience = metadata.get("audience", "")
        errors: list[str] = []

        if missing:
            errors.append(f"thiếu {', '.join(missing)}")
        if doc_id != path.stem:
            errors.append(f"doc_id={doc_id or '<rỗng>'} không khớp tên file")
        if audience and audience not in ALLOWED_AUDIENCES:
            errors.append(f"audience={audience} không hợp lệ")

        document_ids.append(doc_id)
        if audience:
            audiences[audience] += 1

        if errors:
            failures.append(f"{path.name}: {'; '.join(errors)}")
            print(f"{path.name:40} LỖI — {'; '.join(errors)}")
        else:
            print(f"{path.name:40} OK")

    count_ok = 5 <= len(markdown_files) <= 10
    print(f"số file : {len(markdown_files)} — {'OK' if count_ok else 'LỖI (cần 5-10)'}")
    if not count_ok:
        failures.append(f"số file={len(markdown_files)}, yêu cầu 5-10")

    duplicate_ids = sorted(doc_id for doc_id, count in Counter(document_ids).items() if count > 1)
    if duplicate_ids:
        failures.append(f"doc_id trùng: {', '.join(duplicate_ids)}")

    with manifest_path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    csv_ids = [row.get("doc_id", "") for row in rows]
    csv_paths = {row.get("file_path", "") for row in rows}
    expected_paths = {path.as_posix() for path in markdown_files}
    manifest_ok = (
        sorted(csv_ids) == sorted(document_ids)
        and len(csv_ids) == len(set(csv_ids))
        and csv_paths == expected_paths
    )
    print(f"sources.csv: {'OK — khớp 1-1' if manifest_ok else 'LỖI — không khớp corpus'}")
    if not manifest_ok:
        failures.append("sources.csv không khớp 1-1 với các file .md")

    audience_ok = len(audiences) >= 2
    print(f"audience : {dict(sorted(audiences.items()))} — {'OK' if audience_ok else 'LỖI'}")
    if not audience_ok:
        failures.append("audience cần ít nhất hai giá trị khác nhau")

    if failures:
        print("\nKẾT QUẢ: KHÔNG ĐẠT")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nKẾT QUẢ: TẤT CẢ ĐỀU OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
