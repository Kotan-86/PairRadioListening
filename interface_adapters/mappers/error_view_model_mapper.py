# 仕様: docs/spec/interface.md#7.2
from application.errors import GetDialogueError, GetTranscriptError
from interface_adapters.presentation.error_messages import error_message_for
from interface_adapters.view_models.dialogue_view_model import DialogueViewModel
from interface_adapters.view_models.transcript_view_model import TranscriptViewModel


class ErrorViewModelMapper:
    def to_transcript_error_view_model(
        self, lecture_id: str, error: GetTranscriptError
    ) -> TranscriptViewModel:
        return TranscriptViewModel(
            lecture_id=lecture_id,
            lines=(),
            error_message=error_message_for(error),
        )

    def to_dialogue_error_view_model(
        self, lecture_id: str, error: GetDialogueError
    ) -> DialogueViewModel:
        return DialogueViewModel(
            lecture_id=lecture_id,
            lines=(),
            error_message=error_message_for(error),
        )
