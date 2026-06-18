# 仕様: docs/spec/framework.md#5.3
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from interface_adapters.ports.view_model_store import ViewModelStore

TViewModel = TypeVar("TViewModel")
TError = TypeVar("TError")


@dataclass
class LectureViewModelStore(ViewModelStore[TViewModel, TError], Generic[TViewModel, TError]):
    """講義 ID ごとに最新 ViewModel を保持するインメモリ Store。"""

    _models: dict[str, TViewModel] = field(default_factory=dict)

    def present(self, view_model: TViewModel) -> None:
        lecture_id = getattr(view_model, "lecture_id")
        self._models[str(lecture_id)] = view_model

    def present_error(self, error: TError) -> None:
        # Presenter はエラー時も present(エラー用 ViewModel) を使う。Protocol 準拠のため空実装。
        _ = error

    def get(self, lecture_id: str) -> TViewModel | None:
        return self._models.get(lecture_id)
