"""Source-preserving English sentence spans from NLTK's supported model."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nltk.tokenize import PunktTokenizer


@lru_cache(maxsize=1)
def _english_tokenizer() -> PunktTokenizer:
    from nltk.downloader import (  # pyright: ignore[reportMissingTypeStubs]
        download,  # pyright: ignore[reportUnknownVariableType]
    )
    from nltk.tokenize import PunktTokenizer

    try:
        return PunktTokenizer("english")
    except LookupError:
        download("punkt_tab", quiet=True, raise_on_error=True)
        return PunktTokenizer("english")


def sentence_spans(text: str) -> list[tuple[int, int]]:
    return list(_english_tokenizer().span_tokenize(text))
