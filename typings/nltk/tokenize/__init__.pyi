"""NLTK 3.10.3 PunktTokenizer / span_tokenize used by sentences.py."""

from collections.abc import Iterator

class PunktTokenizer:
    def __init__(self, lang: str = "english") -> None: ...
    def span_tokenize(
        self, text: str, realign_boundaries: bool = True
    ) -> Iterator[tuple[int, int]]: ...
