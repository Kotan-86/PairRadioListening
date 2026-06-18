# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
"""
Outbound Port: 講義集約（lecture）の永続化抽象。

Why: ユースケースはドメインのみに依存し、DB 等の具体実装はインフラ層に置く。
     契約（本 Protocol）はアプリケーション層が所有する。
"""
from typing import Protocol

from application.ports.errors import PersistencePortError
from application.result import Result
from domain.entities.entity import EntityId
from domain.entities.lecture import Lecture


class LectureRepository(Protocol):
    """講義集約の読み書きポート。インフラ層が本 Protocol を実装する。"""

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        """講義集約を新規保存または更新する。"""

    def find_by_id(self, lecture_id: EntityId) -> Result[Lecture | None, PersistencePortError]:
        """
        講義 ID で集約を取得する。

        - 存在する: Ok(lecture)
        - 存在しない: Ok(None)（ユースケースが LectureNotFound に変換）
        - インフラ失敗: Err(PersistencePortError)
        """
