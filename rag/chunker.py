"""
RAG Chunker — splits repository source files into overlapping text chunks
suitable for embedding and vector storage.

Strategy:
  - Code files: split on function/class boundaries via regex heuristics first,
    then fall back to recursive character splitting.
  - Markdown/text files: split on heading boundaries, then paragraphs.
  - All chunks are enriched with source metadata (file, language, start_line).

Design decisions:
  - No tree-sitter here (avoids grammar binary downloads at runtime).
    Boundary detection uses reliable regex patterns that work across languages.
  - Chunk size and overlap come from Settings — never hardcoded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from backend.config import get_settings

# ── Language detection ────────────────────────────────────────────────────────

_EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py":    "python",
    ".js":    "javascript",
    ".ts":    "typescript",
    ".jsx":   "javascript",
    ".tsx":   "typescript",
    ".java":  "java",
    ".go":    "go",
    ".rs":    "rust",
    ".rb":    "ruby",
    ".php":   "php",
    ".cs":    "csharp",
    ".cpp":   "cpp",
    ".c":     "c",
    ".md":    "markdown",
    ".txt":   "text",
    ".yaml":  "yaml",
    ".yml":   "yaml",
    ".json":  "json",
    ".toml":  "toml",
    ".sh":    "bash",
    ".sql":   "sql",
}

# Top-level definition patterns per language (for boundary-aware splitting)
_BOUNDARY_PATTERNS: dict[str, str] = {
    "python":     r"^(class |def |async def )",
    "javascript": r"^(function |class |const \w+ = (?:async )?(?:function|\(|[a-z]))",
    "typescript": r"^(function |class |interface |type |const \w+ = (?:async )?(?:function|\(|[a-z]))",
    "java":       r"^(public |private |protected |class |interface |enum )",
    "go":         r"^(func |type |var |const )",
    "rust":       r"^(pub |fn |struct |enum |impl |trait )",
}


def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    return _EXTENSION_TO_LANGUAGE.get(ext, "text")


# ── Chunk dataclass ───────────────────────────────────────────────────────────

@dataclass
class CodeChunk:
    """A single text chunk with full provenance metadata."""
    content:    str
    source:     str            # relative file path
    language:   str
    start_line: int            # 1-indexed
    end_line:   int            # 1-indexed, inclusive
    chunk_index: int           # position within this file's chunks
    metadata:   dict = field(default_factory=dict)

    def to_document_dict(self) -> dict:
        """Convert to the dict format expected by vector stores."""
        return {
            "page_content": self.content,
            "metadata": {
                "source":      self.source,
                "language":    self.language,
                "start_line":  self.start_line,
                "end_line":    self.end_line,
                "chunk_index": self.chunk_index,
                **self.metadata,
            },
        }


# ── Core chunker ──────────────────────────────────────────────────────────────

class RepositoryChunker:
    """
    Splits source files into overlapping chunks for RAG indexing.

    Usage:
        chunker = RepositoryChunker()
        chunks = chunker.chunk_file(content="...", file_path="src/auth.py")
        chunks = chunker.chunk_repository(files={"src/auth.py": "...", ...})
    """

    def __init__(self) -> None:
        settings      = get_settings()
        self._size    = settings.max_chunk_size
        self._overlap = settings.chunk_overlap

    def chunk_file(
        self,
        content: str,
        file_path: str,
        extra_metadata: Optional[dict] = None,
    ) -> list[CodeChunk]:
        """
        Chunk a single file's content.

        Returns an empty list for empty files or binary-looking content.
        """
        if not content or not content.strip():
            return []

        # Skip likely binary files
        if "\x00" in content[:1024]:
            return []

        language = detect_language(file_path)

        if language == "markdown":
            raw_chunks = self._split_markdown(content)
        elif language in _BOUNDARY_PATTERNS:
            raw_chunks = self._split_by_boundaries(content, language)
        else:
            raw_chunks = self._split_recursive(content)

        chunks: list[CodeChunk] = []
        for idx, (text, start_line) in enumerate(raw_chunks):
            if not text.strip():
                continue
            end_line = start_line + text.count("\n")
            chunks.append(CodeChunk(
                content=text,
                source=file_path,
                language=language,
                start_line=start_line,
                end_line=end_line,
                chunk_index=idx,
                metadata=extra_metadata or {},
            ))
        return chunks

    def chunk_repository(
        self,
        files: dict[str, str],
        extra_metadata: Optional[dict] = None,
    ) -> list[CodeChunk]:
        """
        Chunk an entire repository represented as {path: content} dict.
        Skips files that are too large (> 200KB) to avoid embedding noise.
        """
        all_chunks: list[CodeChunk] = []
        for path, content in files.items():
            if len(content) > 200_000:
                continue
            file_chunks = self.chunk_file(content, path, extra_metadata)
            all_chunks.extend(file_chunks)
        return all_chunks

    # ── Splitting strategies ──────────────────────────────────────────────────

    def _split_by_boundaries(
        self, content: str, language: str
    ) -> list[tuple[str, int]]:
        """
        Split at top-level function/class definitions.
        Each block starts at the definition line.
        Falls back to recursive splitting for blocks > chunk_size.
        """
        pattern = _BOUNDARY_PATTERNS[language]
        lines   = content.splitlines(keepends=True)
        blocks: list[tuple[str, int]] = []  # (text, start_line_1indexed)

        current_lines: list[str] = []
        current_start = 1

        for lineno, line in enumerate(lines, start=1):
            if re.match(pattern, line) and current_lines:
                blocks.append(("".join(current_lines), current_start))
                current_lines = [line]
                current_start = lineno
            else:
                current_lines.append(line)

        if current_lines:
            blocks.append(("".join(current_lines), current_start))

        # Recursively split oversized blocks
        result: list[tuple[str, int]] = []
        for text, start in blocks:
            if len(text) <= self._size:
                result.append((text, start))
            else:
                sub = self._split_recursive(text)
                for sub_text, sub_offset in sub:
                    # sub_offset is relative; convert to absolute line number
                    abs_start = start + sub_offset - 1
                    result.append((sub_text, abs_start))
        return result

    def _split_markdown(self, content: str) -> list[tuple[str, int]]:
        """Split markdown on heading boundaries (## / ###)."""
        lines  = content.splitlines(keepends=True)
        blocks: list[tuple[str, int]] = []
        current: list[str] = []
        start = 1

        for lineno, line in enumerate(lines, start=1):
            if re.match(r"^#{1,3} ", line) and current:
                blocks.append(("".join(current), start))
                current = [line]
                start   = lineno
            else:
                current.append(line)

        if current:
            blocks.append(("".join(current), start))

        result: list[tuple[str, int]] = []
        for text, s in blocks:
            if len(text) <= self._size:
                result.append((text, s))
            else:
                result.extend(self._split_recursive(text, base_line=s))
        return result

    def _split_recursive(
        self, content: str, base_line: int = 1
    ) -> list[tuple[str, int]]:
        """
        Recursive character-based split with overlap.
        Tries to split on paragraph boundaries first, then newlines, then chars.
        """
        if len(content) <= self._size:
            return [(content, base_line)]

        # Separator priority: blank line → newline → space → any char
        separators = ["\n\n", "\n", " ", ""]
        for sep in separators:
            if sep and sep in content:
                return self._split_on_separator(content, sep, base_line)

        # Hard split as last resort
        chunks = []
        pos    = 0
        while pos < len(content):
            end  = min(pos + self._size, len(content))
            text = content[pos:end]
            line = base_line + content[:pos].count("\n")
            chunks.append((text, line))
            pos += self._size - self._overlap
        return chunks

    def _split_on_separator(
        self, content: str, sep: str, base_line: int
    ) -> list[tuple[str, int]]:
        """Split content on a separator, respecting chunk size and overlap."""
        parts  = content.split(sep)
        chunks: list[tuple[str, int]] = []
        current = ""
        current_start = base_line
        lines_so_far  = 0

        for part in parts:
            candidate = (current + sep + part) if current else part
            if len(candidate) <= self._size:
                current = candidate
            else:
                if current:
                    chunks.append((current, current_start))
                    # Carry overlap into next chunk
                    overlap_text  = current[-self._overlap:] if self._overlap else ""
                    overlap_lines = overlap_text.count("\n")
                    lines_so_far += current.count("\n")
                    current_start = base_line + lines_so_far - overlap_lines
                    current = overlap_text + sep + part if overlap_text else part
                else:
                    current = part

        if current:
            chunks.append((current, current_start))
        return chunks
