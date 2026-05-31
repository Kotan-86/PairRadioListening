# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from dataclasses import dataclass, field

from application.ports.errors import PersistencePortError
from application.result import Ok, Result
from domain.entities.entity import EntityId
from domain.entities.lecture import Lecture


@dataclass
class InMemoryLectureRepository:
    """LectureRepository Protocol のインメモリ実装。"""

    _store: dict[str, Lecture] = field(default_factory=dict)

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        self._store[str(lecture.id)] = lecture
        return Ok(None)

    def find_by_id(self, lecture_id: EntityId) -> Result[Lecture | None, PersistencePortError]:
        return Ok(self._store.get(str(lecture_id)))
