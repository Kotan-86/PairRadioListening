# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from dataclasses import dataclass, field

from application.ports.errors import PersistencePortError
from application.result import Ok, Result
from domain.entities.entity import EntityId
from domain.entities.reaction import Reaction


@dataclass
class InMemoryReactionRepository:
    """ReactionRepository Protocol のインメモリ実装。"""

    _store: dict[str, dict[str, Reaction]] = field(default_factory=dict)

    def save(self, reaction: Reaction) -> Result[None, PersistencePortError]:
        lecture_key = str(reaction.lecture_id)
        if lecture_key not in self._store:
            self._store[lecture_key] = {}
        self._store[lecture_key][str(reaction.id)] = reaction
        return Ok(None)

    def find_by_id(
        self,
        lecture_id: EntityId,
        reaction_id: EntityId,
    ) -> Result[Reaction | None, PersistencePortError]:
        lecture_reactions = self._store.get(str(lecture_id), {})
        return Ok(lecture_reactions.get(str(reaction_id)))

    def list_by_lecture_id(
        self,
        lecture_id: EntityId,
    ) -> Result[list[Reaction], PersistencePortError]:
        lecture_reactions = self._store.get(str(lecture_id), {})
        return Ok(list(lecture_reactions.values()))
