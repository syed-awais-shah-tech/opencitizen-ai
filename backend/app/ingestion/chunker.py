"""Document chunking engine with provenance preservation and overlap management."""

import re
from typing import Any
from app.ingestion.models import DocumentChunk, ExtractedPage


class DocumentChunker:
    """Splits extracted page text into semantically cohesive, traceable chunks."""

    def __init__(
        self,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
        min_chunk_size: int = 40,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly smaller than chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_page(
        self,
        page: ExtractedPage,
        document_id: str,
        source_filename: str,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Split a single page's text into structured document chunks."""
        text = page.cleaned_text.strip()
        if not text or len(text) < self.min_chunk_size:
            return []

        segments = self._split_text_recursively(text)
        chunks: list[DocumentChunk] = []

        for idx, segment in enumerate(segments):
            chunk_num = idx + 1
            chunk_id = f"chk_{document_id}_p{page.page_number}_{chunk_num:03d}"

            # Vector-search friendly metadata payload
            metadata = {
                **(base_metadata or {}),
                "document_id": document_id,
                "source_filename": source_filename,
                "page_number": page.page_number,
                "chunk_id": chunk_id,
                "chunk_index": idx,
            }

            words = segment.split()
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                source_filename=source_filename,
                page_number=page.page_number,
                chunk_index=idx,
                text=segment,
                character_count=len(segment),
                word_count=len(words),
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    def chunk_pages(
        self,
        pages: list[ExtractedPage],
        document_id: str,
        source_filename: str,
        base_metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """Chunk a sequence of extracted document pages."""
        all_chunks: list[DocumentChunk] = []
        for page in pages:
            if page.is_empty:
                continue
            page_chunks = self.chunk_page(
                page=page,
                document_id=document_id,
                source_filename=source_filename,
                base_metadata=base_metadata,
            )
            all_chunks.extend(page_chunks)
        return all_chunks

    def _split_text_recursively(self, text: str) -> list[str]:
        """Split text respecting paragraph and sentence boundaries with overlap."""
        # 1. If text is already under chunk_size, return it directly
        if len(text) <= self.chunk_size:
            return [text]

        # 2. Split by paragraphs
        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If individual paragraph exceeds chunk_size, split by sentences
            if len(para) > self.chunk_size:
                sentence_chunks = self._split_by_sentences(para)
                for sc in sentence_chunks:
                    if current_len + len(sc) + 1 <= self.chunk_size:
                        current_chunk.append(sc)
                        current_len += len(sc) + 1
                    else:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                        current_chunk = [sc]
                        current_len = len(sc)
            else:
                if current_len + len(para) + 2 <= self.chunk_size:
                    current_chunk.append(para)
                    current_len += len(para) + 2
                else:
                    if current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                    current_chunk = [para]
                    current_len = len(para)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # 3. Apply sliding overlap across chunks if more than one chunk
        return self._apply_overlap(chunks)

    def _split_by_sentences(self, paragraph: str) -> list[str]:
        """Split long paragraph into sentence segments."""
        raw_sentences = re.split(r"(?<=[.?!])\s+", paragraph)
        sentences: list[str] = []
        current = ""

        for s in raw_sentences:
            s = s.strip()
            if not s:
                continue
            if not current:
                current = s
            elif len(current) + len(s) + 1 <= self.chunk_size:
                current += " " + s
            else:
                sentences.append(current)
                current = s

        if current:
            sentences.append(current)

        return sentences

    def _apply_overlap(self, raw_chunks: list[str]) -> list[str]:
        """Add context from the tail of previous chunks to heads of subsequent chunks."""
        if len(raw_chunks) <= 1 or self.chunk_overlap <= 0:
            return raw_chunks

        overlapped_chunks: list[str] = [raw_chunks[0]]

        for i in range(1, len(raw_chunks)):
            prev = raw_chunks[i - 1]
            curr = raw_chunks[i]

            # Grab overlap tokens from end of previous chunk
            prev_words = prev.split()
            overlap_words: list[str] = []
            overlap_len = 0

            for word in reversed(prev_words):
                if overlap_len + len(word) + 1 <= self.chunk_overlap:
                    overlap_words.insert(0, word)
                    overlap_len += len(word) + 1
                else:
                    break

            if overlap_words:
                prefix = " ".join(overlap_words)
                curr_with_overlap = f"{prefix} ... {curr}"
            else:
                curr_with_overlap = curr

            overlapped_chunks.append(curr_with_overlap)

        return overlapped_chunks
