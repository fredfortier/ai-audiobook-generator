"""Used Chatterbox API checked against the uv.lock source revision, tts.py."""

from torch import Tensor

class Conditionals: ...

class ChatterboxTTS:
    sr: int
    conds: Conditionals | None
    @classmethod
    def from_local(cls, ckpt_dir: str, device: str) -> ChatterboxTTS: ...
    def generate(
        self,
        text: str,
        repetition_penalty: float = 1.2,
        min_p: float = 0.05,
        top_p: float = 1.0,
        audio_prompt_path: str | None = None,
        exaggeration: float = 0.5,
        cfg_weight: float = 0.5,
        temperature: float = 0.8,
    ) -> Tensor: ...

def punc_norm(text: str) -> str: ...
