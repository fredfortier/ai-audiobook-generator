"""Chatterbox EnTokenizer: tokenizer.py:20-33 in the locked source revision."""

from torch import Tensor

class EnTokenizer:
    def __init__(self, vocab_file_path: str) -> None: ...
    def text_to_tokens(self, text: str) -> Tensor: ...
