# 仕様: docs/spec/interface.md#6.4
from application.dtos.transcript_item import GetTranscriptResponse
from application.errors import GetTranscriptError
from interface_adapters.presentation.error_messages import error_message_for
from interface_adapters.presentation.time_label_format import format_time_label
from interface_adapters.view_models.transcript_view_model import (
    TranscriptLineView,
    TranscriptViewModel,
)


class TranscriptViewModelMapper:
    def to_view_model(self, response: GetTranscriptResponse) -> TranscriptViewModel:
        lines = tuple(
            TranscriptLineView(
                utterance_id=item.utterance_id,
                time_label=format_time_label(item.time_range),
                speaker_label=item.speaker.display_name,
                body=item.speech_text.text,
            )
            for item in response.items
        )
        return TranscriptViewModel(
            lecture_id=response.lecture_id,
            lines=lines,
            error_message="",
        )

    def to_error_view_model(
        self, lecture_id: str, error: GetTranscriptError
    ) -> TranscriptViewModel:
        return TranscriptViewModel(
            lecture_id=lecture_id,
            lines=(),
            error_message=error_message_for(error),
        )
