# 仕様: docs/spec/domain.md#命名
from dataclasses import dataclass, field
from typing import Union
from uuid import UUID, uuid4

EntityId = Union[UUID, str]


@dataclass(kw_only=True)
class Entity:
    id: EntityId | None = field(default=None)

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = uuid4()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
