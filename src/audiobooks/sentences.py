"""Source-preserving English sentence spans from NLTK's supported model."""

from functools import lru_cache


@lru_cache(maxsize=1)
def _english_tokenizer():
    from nltk.tokenize import PunktTokenizer

    return PunktTokenizer("english")


def sentence_spans(text: str) -> list[tuple[int, int]]:
    return list(_english_tokenizer().span_tokenize(text))
