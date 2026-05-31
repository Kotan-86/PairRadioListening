# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from typing import Protocol

from application.ports.errors import PersistencePortError
from application.result import Result
from domain.entities.entity import EntityId
from domain.entities.reaction import Reaction


class ReactionRepository(Protocol):
    """reaction 集約の読み書きポート。インフラ層が本 Protocol を実装する。"""

    def save(self, reaction: Reaction) -> Result[None, PersistencePortError]:
        """reaction 集約を新規保存または更新する。"""

    def find_by_id(
        self,
        lecture_id: EntityId,
        reaction_id: EntityId,
    ) -> Result[Reaction | None, PersistencePortError]:
        """講義 ID と reaction ID で集約を取得する。"""

    def list_by_lecture_id(
        self,
        lecture_id: EntityId,
    ) -> Result[list[Reaction], PersistencePortError]:
        """講義に属する reaction 一覧を取得する。"""
