# 仕様: docs/spec/interface.md#6.5 / §1.3
from application.dtos.dialogue_item import GetDialogueResponse
from application.errors import GetDialogueError
from interface_adapters.presentation.error_messages import error_message_for
from interface_adapters.presentation.quote_label_format import format_quote_label
from interface_adapters.presentation.time_label_format import format_time_label
from interface_adapters.view_models.dialogue_presentation_context import (
    DialoguePresentationContext,
)
from interface_adapters.view_models.dialogue_view_model import (
    DialogueLineView,
    DialogueViewModel,
)


class DialogueViewModelMapper:
    def to_view_model(
        self,
        response: GetDialogueResponse,
        context: DialoguePresentationContext,
    ) -> DialogueViewModel:
        lines = tuple(
            self._to_line_view(item, context) for item in response.items
        )
        return DialogueViewModel(
            lecture_id=response.lecture_id,
            lines=lines,
            error_message="",
        )

    def to_error_view_model(
        self, lecture_id: str, error: GetDialogueError
    ) -> DialogueViewModel:
        return DialogueViewModel(
            lecture_id=lecture_id,
            lines=(),
            error_message=error_message_for(error),
        )

    def _to_line_view(self, item, context: DialoguePresentationContext) -> DialogueLineView:
        reference_time_label = ""
        reference_quote_label = ""
        kind = item.reply_target.reply_target_kind
        target_id = str(item.reply_target.reply_target_id)

        if kind == "utterance":
            time_range = context.utterance_times.get(target_id)
            if time_range is not None:
                reference_time_label = format_time_label(time_range)
        elif kind == "reaction":
            snippet = context.reaction_snippets.get(target_id)
            if snippet is not None:
                reference_quote_label = format_quote_label(
                    snippet.speaker_label, snippet.excerpt
                )

        return DialogueLineView(
            reaction_id=item.reaction_id,
            speaker_label=item.speaker.display_name,
            body=item.reaction_text.text,
            reference_time_label=reference_time_label,
            reference_quote_label=reference_quote_label,
        )
