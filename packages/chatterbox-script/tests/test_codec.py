"""The codec must reject word loss and preserve literal text across Pandoc parsing."""

import pytest
from chatterbox_script import Parameters, Script, Speech, read_script, write_script


def test_literal_markup_and_verse_survive_without_becoming_formatting() -> None:
    parameters = Parameters(
        exaggeration=0.4,
        cfg_weight=0.5,
        temperature=0.8,
        repetition_penalty=1.2,
        min_p=0.05,
        top_p=1.0,
    )
    text = "*Literal* [brackets] #hash <not>\nSecond line."
    script = Script(
        title="Literal source",
        voices={"n": "builtin"},
        defaults=parameters,
        speech=[Speech(id="s000001", voice="n", parameters=parameters, paragraphs=[text])],
    )
    markdown = write_script(script)
    assert read_script(markdown).speech[0].paragraphs == [text]
    for damaged, reason in [
        (markdown.replace('voice="n"', 'voice="n" voice="n"'), "duplicate attribute"),
        (markdown + "\nLost sentence.\n", "flat speech Divs"),
        (markdown.replace('voice="n"', 'voice="n" speed="2"'), "unknown control"),
    ]:
        with pytest.raises(ValueError, match=reason):
            read_script(damaged)
