# 仕様: docs/spec/interface.md#6.5
from application.dtos.dialogue_item import GetDialogueResponse
from application.dtos.transcript_item import GetTranscriptResponse
from interface_adapters.view_models.dialogue_presentation_context import (
    DialoguePresentationContext,
    ReactionSnippet,
)


def build_dialogue_presentation_context(
    dialogue_response: GetDialogueResponse,
    transcript_response: GetTranscriptResponse,
) -> DialoguePresentationContext:
    utterance_times = {
        item.utterance_id: item.time_range for item in transcript_response.items
    }
    reaction_snippets = {
        item.reaction_id: ReactionSnippet(
            speaker_label=item.speaker.display_name,
            excerpt=item.reaction_text.text,
        )
        for item in dialogue_response.items
    }
    return DialoguePresentationContext(
        utterance_times=utterance_times,
        reaction_snippets=reaction_snippets,
    )
