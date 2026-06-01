# 仕様: docs/spec/interface.md#6.5
from dataclasses import dataclass

from application.dtos.dialogue_item import GetDialogueResponse
from application.errors.use_case_errors import GetDialogueError
from interface_adapters.mappers.dialogue_view_model_mapper import DialogueViewModelMapper
from interface_adapters.ports.view_model_store import ViewModelStore
from interface_adapters.view_models.dialogue_presentation_context import (
    DialoguePresentationContext,
)
from interface_adapters.view_models.dialogue_view_model import DialogueViewModel


@dataclass(frozen=True, slots=True)
class DialoguePresenter:
    _mapper: DialogueViewModelMapper
    _store: ViewModelStore[DialogueViewModel, GetDialogueError]

    def present(
        self,
        response: GetDialogueResponse,
        context: DialoguePresentationContext,
    ) -> None:
        self._store.present(self._mapper.to_view_model(response, context))

    def present_error(self, lecture_id: str, error: GetDialogueError) -> None:
        view_model = self._mapper.to_error_view_model(lecture_id, error)
        self._store.present(view_model)
