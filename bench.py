#!/usr/bin/env python3
"""Run one member's chunking strategy on the shared five-query benchmark.

Every member keeps this file unchanged except for the marked CHUNKER line.
The default lexical embedder has no optional dependencies; use
``--embedding local`` for the multilingual semantic model used in the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Callable

from src import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    HeadingSectionChunker,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
)

ROOT_DIR = Path(__file__).resolve().parent
CORPUS_DIR = ROOT_DIR / "data" / "academic_regulations"
BENCHMARK_PATH = CORPUS_DIR / "benchmark.json"
TOP_K = 3

# Mỗi thành viên chỉ đổi dòng này sang chunker được phân công.
CHUNKER = FixedSizeChunker(chunk_size=800, overlap=150)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def tokenize(text: str) -> list[str]:
    stopwords = {
        "va", "la", "cua", "co", "cho", "tai", "theo", "thi", "duoc",
        "nhung", "cac", "mot", "trong", "ve", "khi", "neu", "phai",
        "sinh", "vien", "truong", "dai", "hoc", "bao", "nhieu", "nao",
    }
    return [
        token
        for token in re.findall(r"[a-z0-9]+", normalize_text(text))
        if len(token) > 1 and token not in stopwords
    ]


class LexicalHashEmbedder:
    """Deterministic, dependency-free embedding for ``python bench.py``."""

    def __init__(self, dim: int = 2048) -> None:
        self.dim = dim
        self._backend_name = "offline Vietnamese lexical hashing"

    def __call__(self, text: str) -> list[float]:
        tokens = tokenize(text)
        features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        vector = [0.0] * self.dim
        for feature in features:
            digest = hashlib.md5(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            vector[index] += 1.5 if "_" in feature else 1.0
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Return YAML-like frontmatter and body separately."""
    raw_text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Thiếu frontmatter: {path}")

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2).strip()


def load_corpus() -> list[tuple[Path, dict[str, str], str]]:
    corpus = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        metadata, content = parse_frontmatter(path)
        if metadata.get("doc_id") != path.stem:
            raise ValueError(f"doc_id không khớp tên file: {path.name}")
        corpus.append((path, metadata, content))
    if not 5 <= len(corpus) <= 10:
        raise ValueError(f"Corpus phải có 5-10 tài liệu, hiện có {len(corpus)}")
    return corpus


def make_documents(
    corpus: list[tuple[Path, dict[str, str], str]],
) -> list[Document]:
    documents: list[Document] = []
    for path, frontmatter, content in corpus:
        for index, chunk in enumerate(CHUNKER.chunk(content)):
            documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    metadata={
                        **frontmatter,
                        "doc_id": path.stem,
                        "chunk_index": index,
                        "chunk_strategy": type(CHUNKER).__name__,
                    },
                )
            )
    return documents


def print_results(label: str, results: list[dict]) -> None:
    print(label)
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        preview = " ".join(result["content"].split())[:140]
        print(
            f"  {rank}. score={result['score']:.6f} "
            f"doc_id={metadata.get('doc_id')} chunk={metadata.get('chunk_index')}"
        )
        print(f"     {preview}")


def print_baseline(corpus: list[tuple[Path, dict[str, str], str]]) -> None:
    selected_ids = {
        "tvu-course-registration",
        "tdmu-grade-appeal",
        "tnut-advanced-registration",
    }
    comparator = ChunkingStrategyComparator()
    print("\nBASELINE (frontmatter đã được loại bỏ, chunk_size=500)")
    for path, _, content in corpus:
        if path.stem not in selected_ids:
            continue
        comparison = comparator.compare(content, chunk_size=500)
        stats = ", ".join(
            f"{name}={value['count']} chunks/{value['avg_length']:.2f} ký tự"
            for name, value in comparison.items()
        )
        print(f"- {path.stem}: {stats}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the shared academic benchmark.")
    parser.add_argument("--embedding", choices=("lexical", "local"), default="lexical")
    parser.add_argument("--baseline", action="store_true", help="Print baseline analysis too.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus = load_corpus()
    documents = make_documents(corpus)
    embedding_fn: Callable[[str], list[float]] = (
        LocalEmbedder() if args.embedding == "local" else LexicalHashEmbedder()
    )
    store = EmbeddingStore(collection_name="personal-benchmark", embedding_fn=embedding_fn)
    store.add_documents(documents)
    benchmarks = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

    lengths = [len(document.content) for document in documents]
    average = sum(lengths) / len(lengths) if lengths else 0.0
    print(f"Chunker: {type(CHUNKER).__name__}")
    print(f"Embedding: {embedding_fn._backend_name}")
    print(f"Đã nạp: {store.get_collection_size()} chunks; độ dài TB: {average:.2f}")

    if args.baseline:
        print_baseline(corpus)

    for benchmark in benchmarks:
        query = benchmark["query"]
        metadata_filter = benchmark.get("metadata_filter")
        print(f"\n[{benchmark['id']}] {query}")
        print(f"Gold: {benchmark['gold_answer']}")
        if metadata_filter:
            print_results("Top-3 KHÔNG lọc:", store.search(query, top_k=TOP_K))
        results = store.search_with_filter(
            query,
            top_k=TOP_K,
            metadata_filter=metadata_filter,
        )
        label = f"Top-3 filter={metadata_filter}:" if metadata_filter else "Top-3:"
        print_results(label, results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
