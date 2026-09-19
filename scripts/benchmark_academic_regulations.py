#!/usr/bin/env python3
"""Reproducible benchmark for the K4-L3A academic-regulations corpus.

All four strategies use the same corpus, queries, hashing embedder and top_k.
The dependency-free hashing embedder is lexical rather than semantic; replace it
with LocalEmbedder for the final presentation when sentence-transformers is
available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import Callable

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import (  # noqa: E402
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    HeadingSectionChunker,
    KnowledgeBaseAgent,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
)

CORPUS_DIR = ROOT_DIR / "data" / "academic_regulations"
BENCHMARK_PATH = CORPUS_DIR / "benchmark.json"
TOP_K = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark four chunking strategies.")
    parser.add_argument(
        "--embedding",
        choices=("lexical", "local"),
        default="lexical",
        help="Embedding backend; local requires requirements-local.txt and the cached model.",
    )
    return parser.parse_args()


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
    """Small offline hashing-vectorizer used for reproducible group runs."""

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
    raw_text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Missing frontmatter: {path}")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2).strip()


def load_corpus() -> list[tuple[dict[str, str], str]]:
    corpus = [parse_frontmatter(path) for path in sorted(CORPUS_DIR.glob("*.md"))]
    required_fields = {
        "doc_id", "title", "audience", "source_url", "retrieved_at",
        "document_version", "department", "category", "language",
    }
    if not 5 <= len(corpus) <= 10:
        raise ValueError(f"Corpus must contain 5-10 documents, found {len(corpus)}")
    doc_ids = [metadata.get("doc_id") for metadata, _ in corpus]
    if len(doc_ids) != len(set(doc_ids)):
        raise ValueError("Corpus contains duplicate doc_id values")
    for metadata, _ in corpus:
        missing = required_fields - metadata.keys()
        if missing:
            raise ValueError(f"{metadata.get('doc_id', 'unknown')} is missing {sorted(missing)}")
    audiences = {metadata["audience"] for metadata, _ in corpus}
    if len(audiences) < 2:
        raise ValueError("Corpus needs at least two audience values for filter evaluation")
    return corpus


def make_documents(
    corpus: list[tuple[dict[str, str], str]],
    chunker: object,
    strategy_name: str,
) -> list[Document]:
    documents: list[Document] = []
    for metadata, content in corpus:
        chunks = chunker.chunk(content)
        for index, chunk in enumerate(chunks):
            documents.append(
                Document(
                    id=f"{metadata['doc_id']}#{index}",
                    content=chunk,
                    metadata={
                        **metadata,
                        "doc_id": metadata["doc_id"],
                        "chunk_index": index,
                        "chunk_strategy": strategy_name,
                    },
                )
            )
    return documents


def extractive_llm(prompt: str) -> str:
    """Select the most query-relevant context sentences without an API key."""
    question_match = re.search(r"CÂU HỎI:\s*(.*?)\n\nTRẢ LỜI:", prompt, flags=re.DOTALL)
    question = question_match.group(1) if question_match else ""
    question_tokens = set(tokenize(question))
    context = prompt.split("NGỮ CẢNH:\n", 1)[-1].split("\n\nCÂU HỎI:", 1)[0]
    candidates: list[tuple[float, str]] = []
    for source_number, block in re.findall(
        r"\[(\d+)\] Nguồn:.*?\n(.*?)(?=\n\n\[\d+\] Nguồn:|$)",
        context,
        flags=re.DOTALL,
    ):
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", block):
            sentence = sentence.strip(" -")
            if not sentence or sentence.startswith("#"):
                continue
            sentence_tokens = set(tokenize(sentence))
            overlap = len(question_tokens & sentence_tokens)
            score = overlap / max(1, len(question_tokens))
            if overlap:
                candidates.append((score, f"{sentence} [{source_number}]"))
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected: list[str] = []
    for _, sentence in candidates:
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) == 4:
            break
    return " ".join(selected) if selected else "Không tìm thấy thông tin trong ngữ cảnh được cung cấp."


def contains_terms(text: str, terms: list[str]) -> bool:
    normalized_text = normalize_text(text)
    return all(normalize_text(term) in normalized_text for term in terms)


def run_strategy(
    name: str,
    chunker: object,
    corpus: list[tuple[dict[str, str], str]],
    benchmarks: list[dict],
    embedding_fn: Callable[[str], list[float]],
) -> dict:
    documents = make_documents(corpus, chunker, name)
    store = EmbeddingStore(collection_name=f"academic-{name}", embedding_fn=embedding_fn)
    store.add_documents(documents)
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
    query_results = []
    total_points = 0

    for benchmark in benchmarks:
        metadata_filter = benchmark.get("metadata_filter")
        unfiltered_results = (
            store.search(benchmark["query"], top_k=TOP_K) if metadata_filter else []
        )
        if metadata_filter:
            results = store.search_with_filter(
                benchmark["query"], top_k=TOP_K, metadata_filter=metadata_filter
            )
        else:
            results = store.search(benchmark["query"], top_k=TOP_K)

        expected_ids = set(benchmark["expected_doc_ids"])
        relevant_rank = next(
            (
                index
                for index, result in enumerate(results, start=1)
                if result["metadata"].get("doc_id") in expected_ids
            ),
            None,
        )
        answer = agent.answer(
            benchmark["query"], top_k=TOP_K, metadata_filter=metadata_filter
        )
        answer_correct = contains_terms(answer, benchmark["answer_terms"])
        points = 2 if relevant_rank == 1 and answer_correct else 1 if relevant_rank else 0
        total_points += points
        query_results.append(
            {
                "id": benchmark["id"],
                "query": benchmark["query"],
                "metadata_filter": metadata_filter,
                "unfiltered_top_3": [
                    result["metadata"].get("doc_id") for result in unfiltered_results
                ],
                "top_3": [
                    {
                        "rank": rank,
                        "doc_id": result["metadata"].get("doc_id"),
                        "chunk_index": result["metadata"].get("chunk_index"),
                        "score": round(result["score"], 6),
                        "preview": result["content"][:180].replace("\n", " "),
                    }
                    for rank, result in enumerate(results, start=1)
                ],
                "relevant_rank": relevant_rank,
                "agent_answer": answer,
                "agent_answer_correct": answer_correct,
                "points": points,
            }
        )

    lengths = [len(document.content) for document in documents]
    return {
        "strategy": name,
        "chunk_count": len(documents),
        "avg_chunk_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "retrieval_points": total_points,
        "queries": query_results,
    }


def main() -> int:
    args = parse_args()
    corpus = load_corpus()
    benchmarks = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    embedding_fn = LocalEmbedder() if args.embedding == "local" else LexicalHashEmbedder()
    strategies = {
        "member_1_fixed_size": FixedSizeChunker(chunk_size=800, overlap=150),
        "member_2_sentence": SentenceChunker(max_sentences_per_chunk=3),
        "member_3_recursive": RecursiveChunker(chunk_size=500),
        "member_4_heading_section": HeadingSectionChunker(chunk_size=500),
    }
    output = {
        "corpus_documents": len(corpus),
        "embedding_backend": embedding_fn._backend_name,
        "top_k": TOP_K,
        "results": [
            run_strategy(name, chunker, corpus, benchmarks, embedding_fn)
            for name, chunker in strategies.items()
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
