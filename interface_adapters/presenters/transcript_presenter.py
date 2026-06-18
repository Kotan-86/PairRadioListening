# 仕様: docs/spec/interface.md#6.4
from dataclasses import dataclass

from application.dtos.transcript_item import GetTranscriptResponse
from application.errors.use_case_errors import GetTranscriptError
from interface_adapters.mappers.transcript_view_model_mapper import TranscriptViewModelMapper
from interface_adapters.ports.view_model_store import ViewModelStore
from interface_adapters.view_models.transcript_view_model import TranscriptViewModel


@dataclass(frozen=True, slots=True)
class TranscriptPresenter:
    _mapper: TranscriptViewModelMapper
    _store: ViewModelStore[TranscriptViewModel, GetTranscriptError]

    def present(self, response: GetTranscriptResponse) -> None:
        self._store.present(self._mapper.to_view_model(response))

    def present_error(self, lecture_id: str, error: GetTranscriptError) -> None:
        view_model = self._mapper.to_error_view_model(lecture_id, error)
        self._store.present(view_model)
