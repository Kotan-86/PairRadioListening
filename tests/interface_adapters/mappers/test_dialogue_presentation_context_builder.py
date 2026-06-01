# 仕様: docs/spec/interface.md#6.5
from interface_adapters.mappers.dialogue_presentation_context_builder import (
    build_dialogue_presentation_context,
)
from tests.interface_adapters.conftest import (
    make_dialogue_item,
    make_get_dialogue_response,
    make_get_transcript_response,
    make_transcript_item,
)


def test_build_dialogue_presentation_context_from_responses():
    transcript = make_get_transcript_response(
        items=(make_transcript_item(utterance_id="u1", start_ms=100, end_ms=200),)
    )
    dialogue = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reaction_id="r1",
                speaker_name="ユーザー",
                body="コメント",
            ),
        )
    )

    context = build_dialogue_presentation_context(dialogue, transcript)

    assert context.utterance_times["u1"].start_ms == 100
    assert context.reaction_snippets["r1"].speaker_label == "ユーザー"
    assert context.reaction_snippets["r1"].excerpt == "コメント"
