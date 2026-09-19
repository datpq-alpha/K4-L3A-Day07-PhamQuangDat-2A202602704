from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split after sentence-ending punctuation so that the punctuation remains
        # attached to the sentence instead of being consumed by the regex.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\r?\n+)", text.strip())
            if sentence.strip()
        ]

        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk]).strip()
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text or not current_text.strip():
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        # With no usable separator left, fall back to a safe fixed-size split.
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        lower_priority_separators = remaining_separators[1:]

        if separator not in current_text:
            return self._split(current_text, lower_priority_separators)

        raw_parts = current_text.split(separator)
        pieces: list[str] = []

        for index, part in enumerate(raw_parts):
            if not part:
                continue

            # Reattach the delimiter to preserve sentence/paragraph boundaries.
            piece = part + (separator if index < len(raw_parts) - 1 else "")
            if len(piece) > self.chunk_size:
                pieces.extend(self._split(piece, lower_priority_separators))
            else:
                pieces.append(piece)

        # Merge adjacent small pieces back up to the configured size. Without
        # this step, documents containing many short lines produce tiny chunks.
        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            if buffer and len(buffer) + len(piece) > self.chunk_size:
                chunks.append(buffer.strip())
                buffer = piece
            else:
                buffer += piece

        if buffer.strip():
            chunks.append(buffer.strip())

        return chunks


class HeadingSectionChunker:
    """Split Markdown at headings and preserve section context.

    The document's level-one heading is prepended to every section. When a
    section is longer than ``chunk_size``, its own heading is also prepended to
    every recursively split child so later children do not lose their topic.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections = [
            section.strip()
            for section in re.split(r"(?=^#{1,6}\s)", text, flags=re.MULTILINE)
            if section.strip()
        ]
        chunks: list[str] = []
        root_heading = ""

        for section in sections:
            lines = section.splitlines()
            heading = lines[0].strip() if lines and lines[0].lstrip().startswith("#") else ""
            body = "\n".join(lines[1:] if heading else lines).strip()

            if heading.startswith("# "):
                root_heading = heading
                if not body:
                    continue

            headings = list(dict.fromkeys(item for item in (root_heading, heading) if item))
            prefix = "\n".join(headings)
            combined = f"{prefix}\n\n{body}".strip() if prefix else body

            if len(combined) <= self.chunk_size:
                chunks.append(combined)
                continue

            repeated_prefix = f"{prefix}\n\n" if prefix else ""
            body_limit = max(1, self.chunk_size - len(repeated_prefix))
            for child in RecursiveChunker(chunk_size=body_limit).chunk(body):
                chunks.append(f"{repeated_prefix}{child}".strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        safe_chunk_size = max(1, chunk_size)
        overlap = min(50, max(0, safe_chunk_size // 10))
        strategy_chunks = {
            "fixed_size": FixedSizeChunker(safe_chunk_size, overlap).chunk(text),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3).chunk(text),
            "recursive": RecursiveChunker(chunk_size=safe_chunk_size).chunk(text),
        }

        comparison: dict[str, dict] = {}
        for strategy_name, chunks in strategy_chunks.items():
            count = len(chunks)
            comparison[strategy_name] = {
                "count": count,
                "avg_length": sum(len(chunk) for chunk in chunks) / count if count else 0.0,
                "chunks": chunks,
            }
        return comparison
