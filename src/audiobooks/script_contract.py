"""Original Chatterbox script records and their single Pandoc codec."""

from __future__ import annotations

import io
from typing import Literal, Self

import panflute as pf
import pypandoc
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, model_validator

DIALECT = "markdown_strict+fenced_divs+yaml_metadata_block"
CONTROLS = ("exaggeration", "cfg_weight", "temperature", "repetition_penalty", "min_p", "top_p")


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Parameters(Record):
    exaggeration: float = Field(ge=0.3, le=1.1)
    cfg_weight: float = Field(ge=0.25, le=0.6)
    temperature: float = Field(ge=0.5, le=0.9)
    repetition_penalty: float = Field(ge=1, le=2)
    min_p: float = Field(ge=0, le=1)
    top_p: float = Field(gt=0, le=1)


class Speech(Record):
    id: str = Field(pattern=r"^s[0-9]{6,}$")
    voice: str = Field(min_length=1)
    parameters: Parameters
    paragraphs: list[str] = Field(min_length=1)
    heading_level: int | None = Field(default=None, ge=1, le=6)

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        if any(not p.strip() for p in self.paragraphs):
            raise ValueError("empty speech paragraph")
        if any(
            p != "\n".join(" ".join(line.split()) for line in p.split("\n"))
            for p in self.paragraphs
        ):
            raise ValueError("speech requires single spaces and explicit verse line breaks")
        if self.heading_level is not None and len(self.paragraphs) != 1:
            raise ValueError("a heading must be the only body element")
        return self


class Script(Record):
    adapt_text_version: Literal[1] = 1
    title: str
    engine: Literal["chatterbox-original"] = "chatterbox-original"
    language: Literal["en"] = "en"
    voices: dict[str, str]
    defaults: Parameters
    speech: list[Speech]

    @model_validator(mode="after")
    def validate_voice_bindings(self) -> Self:
        ids = [s.id for s in self.speech]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate speech IDs")
        if not self.voices or any(not k or not v for k, v in self.voices.items()):
            raise ValueError("empty voice registry or binding")
        if any(s.voice not in self.voices for s in self.speech):
            raise ValueError("unregistered speech voice")
        return self


def convert_document(value: str | pf.Doc, input_format: str, output_format: str) -> str:
    converted = pf.convert_text(
        value,
        input_format=input_format,
        output_format=output_format,
        standalone=True,
        pandoc_path=pypandoc.get_pandoc_path(),
        extra_args=["--fail-if-warnings"] + (["--wrap=none"] if output_format == DIALECT else []),
    )

    if not isinstance(converted, str):
        raise ValueError("document conversion requires a text output format")
    return converted


def literal_inlines(text: str) -> list[pf.Inline]:
    """Preserve punctuation and verse breaks as literal nodes, without reparsing."""
    nodes: list[pf.Inline] = []
    for n, line in enumerate(text.split("\n")):
        if n:
            nodes.append(pf.LineBreak())
        for i, word in enumerate(line.split(" ")):
            if i:
                nodes.append(pf.Space())
            if word:
                nodes.append(pf.Str(word))
    return nodes


def project_text(element: pf.Element) -> str:
    if isinstance(element, pf.Str):
        return element.text
    if isinstance(element, (pf.Space, pf.SoftBreak)):
        return " "
    if isinstance(element, pf.LineBreak):
        return "\n"
    if isinstance(element, (pf.Emph, pf.Strong, pf.Quoted, pf.Span, pf.Para, pf.Plain, pf.Header)):
        if isinstance(element, pf.Span) and (
            element.attributes or element.classes or element.identifier
        ):
            raise ValueError("attributed inline spans are unsupported")
        return "".join(project_text(child) for child in element.content)
    raise ValueError(f"unsupported spoken element: {type(element).__name__}")


def write_script(script: Script) -> str:
    blocks: list[pf.Block] = []
    for s in script.speech:
        attrs = {"voice": s.voice}
        attrs.update(
            {
                k: str(v)
                for k, v in s.parameters.model_dump().items()
                if v != script.defaults.model_dump()[k]
            }
        )
        body = (
            [pf.Header(*literal_inlines(s.paragraphs[0]), level=s.heading_level)]
            if s.heading_level
            else [pf.Para(*literal_inlines(p)) for p in s.paragraphs]
        )
        blocks.append(pf.Div(*body, identifier=s.id, classes=["speech"], attributes=attrs))
    metadata = script.model_dump(exclude={"speech"})
    doc = pf.Doc(*blocks, metadata=metadata)
    return convert_document(doc, "panflute", DIALECT)


def parse_document(markdown: str) -> pf.Doc:
    # Inspect Pandoc attributes before Panflute turns their pairs into a dictionary.
    raw = convert_document(markdown, DIALECT, "json")
    ast: JsonValue = TypeAdapter[JsonValue](JsonValue).validate_json(raw)

    def check_attributes(node: JsonValue) -> None:
        if isinstance(node, dict):
            kind = node.get("t")
            if isinstance(kind, str) and kind in {
                "Div",
                "Span",
                "Header",
                "Code",
                "CodeBlock",
                "Link",
                "Image",
            }:
                content = node["c"]
                if not isinstance(content, list):
                    raise ValueError("malformed Pandoc attribute-bearing node")
                _, _, pairs = TypeAdapter(
                    tuple[str, list[str], list[tuple[str, str]]]
                ).validate_python(content[1 if kind == "Header" else 0])
                keys = [pair[0] for pair in pairs]
                if len(keys) != len(set(keys)):
                    raise ValueError("duplicate attribute keys")
            for child in node.values():
                check_attributes(child)
        elif isinstance(node, list):
            for child in node:
                check_attributes(child)

    check_attributes(ast)
    return pf.load(io.StringIO(raw))


class ScriptMetadata(Record):
    adapt_text_version: int | str
    title: str
    engine: Literal["chatterbox-original"]
    language: Literal["en"]
    voices: dict[str, str]
    defaults: dict[str, float | int | str]


def read_script(markdown: str) -> Script:
    doc = parse_document(markdown)
    metadata = doc.get_metadata()
    allowed = set(Script.model_fields) - {"speech"}
    if set(metadata) != allowed:
        raise ValueError(f"invalid metadata fields: {set(metadata) ^ allowed}")
    fields = ScriptMetadata.model_validate(metadata)
    version = int(fields.adapt_text_version)
    defaults = Parameters.model_validate({k: float(v) for k, v in fields.defaults.items()})
    speech: list[Speech] = []
    for block in doc.content:
        if not isinstance(block, pf.Div) or list(block.classes) != ["speech"]:
            raise ValueError("all audible content must be in flat speech Divs")
        if set(block.attributes) - {"voice", *CONTROLS} or "voice" not in block.attributes:
            raise ValueError("unknown control or missing voice")
        body = list(block.content)
        heading = len(body) == 1 and isinstance(body[0], pf.Header)
        if not body or (not heading and any(not isinstance(p, pf.Para) for p in body)):
            raise ValueError("speech body must contain paragraphs or one heading")
        params = defaults.model_dump()
        params.update({k: float(v) for k, v in block.attributes.items() if k != "voice"})
        speech.append(
            Speech(
                id=block.identifier,
                voice=block.attributes["voice"],
                parameters=Parameters.model_validate(params),
                paragraphs=[project_text(paragraph) for paragraph in body],
                heading_level=(
                    body[0].level if len(body) == 1 and isinstance(body[0], pf.Header) else None
                ),
            )
        )
    return Script.model_validate(
        {
            **fields.model_dump(),
            "adapt_text_version": version,
            "defaults": defaults,
            "speech": speech,
        }
    )
