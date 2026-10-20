"""Used Panflute 2.3.1 API, checked against base.py, elements.py and tools.py."""

from collections.abc import Sequence
from typing import TextIO

from pydantic import JsonValue

class Element:
    content: Sequence[Element]

class Inline(Element): ...
class Block(Element): ...

class Str(Inline):
    text: str
    def __init__(self, text: str) -> None: ...

class Space(Inline): ...
class SoftBreak(Inline): ...
class LineBreak(Inline): ...
class Emph(Inline): ...
class Strong(Inline): ...
class Quoted(Inline): ...

class Span(Inline):
    identifier: str
    classes: Sequence[str]
    attributes: dict[str, str]

class Para(Block):
    def __init__(self, *args: Inline) -> None: ...

class Plain(Block): ...

class Header(Block):
    level: int
    def __init__(
        self,
        *args: Inline,
        level: int = 1,
        identifier: str = "",
        classes: Sequence[str] = ...,
        attributes: dict[str, str] = ...,
    ) -> None: ...

class Div(Block):
    identifier: str
    classes: Sequence[str]
    attributes: dict[str, str]
    def __init__(
        self,
        *args: Block,
        identifier: str = "",
        classes: Sequence[str] = ...,
        attributes: dict[str, str] = ...,
    ) -> None: ...

class Doc(Element):
    def __init__(
        self,
        *args: Block,
        metadata: dict[str, object] = ...,
        format: str = "html",
        api_version: tuple[int, ...] = ...,
    ) -> None: ...
    def get_metadata(self) -> dict[str, JsonValue]: ...

def convert_text(
    text: str | Doc,
    input_format: str = "markdown",
    output_format: str = "panflute",
    standalone: bool = False,
    extra_args: list[str] | None = None,
    pandoc_path: str | None = None,
) -> str | Doc | list[Element]: ...
def load(input_stream: TextIO | None = None) -> Doc: ...
