"""Physical generation spans; editorial text and semantic beats remain unchanged."""
from collections.abc import Sequence

from audiobooks.sentences import sentence_spans


def generation_spans(text: str, tokenizer, token_limit: int,
                     reviewed_clause_cuts: Sequence[int] = ()) -> list[tuple[int, int]]:
    """Pack sentences using original Chatterbox counts and explicit reviewed cuts.

    Spans cover the complete original string, including boundary whitespace.
    Generate from each span's stripped raw text, not its token-counting view.
    Caller records the source-grounded review of exceptional clause cuts.
    """
    from chatterbox.tts import punc_norm

    if not text.strip() or type(token_limit) is not int or token_limit < 1:
        raise ValueError('nonempty text and positive integer token limit required')
    cuts = list(reviewed_clause_cuts)
    if cuts != sorted(set(cuts)) or any(
        type(cut) is not int or not 0 < cut < len(text)
        or not text[cut - 1].isspace() or text[cut].isspace() for cut in cuts
    ):
        raise ValueError('reviewed cuts must be ordered original offsets at word starts')
    boundaries = sorted({0, len(text), *cuts,
                         *(start for start, _ in sentence_spans(text))})

    def count(start, end):
        return int(tokenizer.text_to_tokens(punc_norm(text[start:end].strip())).shape[-1])

    packed = []
    start = boundaries[0]
    end = start
    for left, right in zip(boundaries, boundaries[1:]):
        if not text[left:right].strip():
            continue
        tokens = count(left, right)
        if tokens > token_limit:
            raise ValueError(f'original span [{left}, {right}) has {tokens} native tokens; '
                             f'limit {token_limit}; review a clause boundary or the budget')
        if end > start and count(start, right) > token_limit:
            packed.append((start, end))
            start = left
        end = right
    packed.append((start, len(text)))
    if packed[0][0] != 0 or any(a[1] != b[0] for a, b in zip(packed, packed[1:])):
        raise ValueError('generation spans do not cover original text')
    return packed
