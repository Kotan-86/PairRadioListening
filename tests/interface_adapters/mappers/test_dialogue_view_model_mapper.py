# 仕様: docs/spec/interface.md#6.7 / §7.5
from dataclasses import fields

from interface_adapters.mappers.dialogue_view_model_mapper import DialogueViewModelMapper
from interface_adapters.presentation.error_messages import QUOTE_EXCERPT_MAX_LENGTH
from interface_adapters.presentation.quote_label_format import format_quote_label
from interface_adapters.presentation.time_label_format import format_time_label
from interface_adapters.view_models.dialogue_presentation_context import (
    DialoguePresentationContext,
    ReactionSnippet,
)
from interface_adapters.view_models.dialogue_view_model import DialogueLineView
from domain.value_objects.time_range import TimeRange
from tests.interface_adapters.conftest import make_dialogue_item, make_get_dialogue_response


def _context(
    *,
    utterance_times: dict[str, TimeRange] | None = None,
    reaction_snippets: dict[str, ReactionSnippet] | None = None,
) -> DialoguePresentationContext:
    return DialoguePresentationContext(
        utterance_times=utterance_times or {},
        reaction_snippets=reaction_snippets or {},
    )


def test_dialogue_mapper_line_count_matches_items():
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(reaction_id="r1", dialogue_sequence=0),
            make_dialogue_item(reaction_id="r2", dialogue_sequence=1),
        )
    )
    mapper = DialogueViewModelMapper()

    view_model = mapper.to_view_model(response, _context())

    assert len(view_model.lines) == len(response.items)


def test_utterance_reply_target_sets_time_label_only():
    time_range = TimeRange(start_ms=0, end_ms=1000)
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reply_target_kind="utterance",
                reply_target_id="u1",
            ),
        )
    )
    mapper = DialogueViewModelMapper()

    view_model = mapper.to_view_model(
        response,
        _context(utterance_times={"u1": time_range}),
    )
    line = view_model.lines[0]

    assert line.reference_time_label == format_time_label(time_range)
    assert line.reference_quote_label == ""


def test_reaction_reply_target_sets_quote_label_only():
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reply_target_kind="reaction",
                reply_target_id="r0",
            ),
        )
    )
    mapper = DialogueViewModelMapper()
    snippet = ReactionSnippet(speaker_label="ユーザー", excerpt="過去の投稿")

    view_model = mapper.to_view_model(
        response,
        _context(reaction_snippets={"r0": snippet}),
    )
    line = view_model.lines[0]

    assert line.reference_time_label == ""
    assert line.reference_quote_label == format_quote_label(
        snippet.speaker_label, snippet.excerpt
    )


def test_reference_labels_are_mutually_exclusive():
    time_range = TimeRange(start_ms=0, end_ms=1000)
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reaction_id="r-utt",
                reply_target_kind="utterance",
                reply_target_id="u1",
            ),
            make_dialogue_item(
                reaction_id="r-react",
                reply_target_kind="reaction",
                reply_target_id="r0",
            ),
        )
    )
    mapper = DialogueViewModelMapper()

    view_model = mapper.to_view_model(
        response,
        _context(
            utterance_times={"u1": time_range},
            reaction_snippets={
                "r0": ReactionSnippet(speaker_label="AI", excerpt="返信先")
            },
        ),
    )

    for line in view_model.lines:
        assert not (
            line.reference_time_label != "" and line.reference_quote_label != ""
        )


def test_reaction_quote_label_does_not_include_lecture_time_label():
    time_range = TimeRange(start_ms=0, end_ms=1000)
    time_label = format_time_label(time_range)
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reply_target_kind="reaction",
                reply_target_id="r0",
            ),
        )
    )
    mapper = DialogueViewModelMapper()

    view_model = mapper.to_view_model(
        response,
        _context(
            utterance_times={"u1": time_range},
            reaction_snippets={"r0": ReactionSnippet(speaker_label="AI", excerpt="text")},
        ),
    )

    assert time_label not in view_model.lines[0].reference_quote_label


def test_missing_reference_keys_yield_empty_labels_without_error():
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reply_target_kind="utterance",
                reply_target_id="missing-u",
            ),
            make_dialogue_item(
                reply_target_kind="reaction",
                reply_target_id="missing-r",
            ),
        )
    )
    mapper = DialogueViewModelMapper()

    view_model = mapper.to_view_model(response, _context())

    for line in view_model.lines:
        assert line.reference_time_label == ""
        assert line.reference_quote_label == ""


def test_dialogue_line_view_has_no_dialogue_sequence_field():
    field_names = {field.name for field in fields(DialogueLineView)}

    assert "dialogue_sequence" not in field_names


def test_long_excerpt_is_truncated_in_quote_label():
    long_text = "あ" * (QUOTE_EXCERPT_MAX_LENGTH + 5)
    response = make_get_dialogue_response(
        items=(
            make_dialogue_item(
                reply_target_kind="reaction",
                reply_target_id="r0",
            ),
        )
    )
    mapper = DialogueViewModelMapper()

    view_model = mapper.to_view_model(
        response,
        _context(
            reaction_snippets={
                "r0": ReactionSnippet(speaker_label="ユーザー", excerpt=long_text)
            }
        ),
    )

    assert view_model.lines[0].reference_quote_label.endswith("…")
