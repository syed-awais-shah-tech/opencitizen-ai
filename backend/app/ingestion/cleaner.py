"""Text cleaning and normalization utilities for extracted PDF content."""

import re
import unicodedata


class TextCleaner:
    """Sanitizes raw text extracted from PDF documents."""

    def __init__(self, min_page_chars: int = 15) -> None:
        self.min_page_chars = min_page_chars

    def clean(self, raw_text: str | None) -> str:
        """Normalize and clean raw extracted text."""
        if not raw_text:
            return ""

        # 1. Normalize Unicode compatibility decomposition/composition (NFKC)
        text = unicodedata.normalize("NFKC", raw_text)

        # 2. Normalize carriage returns and line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Remove null characters and non-printable control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # 4. Remove replacement characters (\ufffd)
        text = text.replace("\ufffd", "")

        # 5. Fix hyphenated line breaks (e.g. 'com-\nmittee' -> 'committee')
        text = re.sub(r"(\b[a-zA-Z]{2,})-\n([a-zA-Z]{2,}\b)", r"\1\2", text)

        # 6. Collapse excessive inline whitespace (spaces/tabs), preserving newlines
        text = re.sub(r"[^\S\n]+", " ", text)

        # 7. Collapse more than two consecutive newlines into double newlines (paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def is_insufficient(self, text: str) -> bool:
        """Determine if cleaned text has little or no meaningful textual content."""
        # Strip all whitespaces and punctuation to check for real alphanumeric content
        alphanumeric = re.sub(r"\W+", "", text)
        return len(alphanumeric) < self.min_page_chars
