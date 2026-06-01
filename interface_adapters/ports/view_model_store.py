# 仕様: docs/spec/interface.md#6.2
from typing import Protocol, TypeVar

TViewModel = TypeVar("TViewModel")
TError = TypeVar("TError")


class ViewModelStore(Protocol[TViewModel, TError]):
    def present(self, view_model: TViewModel) -> None: ...

    def present_error(self, error: TError) -> None: ...
