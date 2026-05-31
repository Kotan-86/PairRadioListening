# 仕様: docs/spec/application.md#generate_ai_reactions_for_utterance
from typing import Protocol

from application.ports.errors import ReactionTextPortError
from application.result import Result
from domain.entities.reaction import Reaction
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.dialogue_policies import (
    LecturerReactionPolicy,
    UserReactionResponsePolicy,
)


class ReactionTextGeneratorPort(Protocol):
    """AI reaction 本文生成ポート。LLM 等の具体実装はインフラ層が担う。"""

    def generate_for_lecturer_reaction(
        self,
        policy: LecturerReactionPolicy,
        utterance: Utterance,
        persona: AiPersonaProfile,
    ) -> Result[str, ReactionTextPortError]:
        """講師発話に対する AI reaction 本文を生成する。"""

    def generate_for_user_reaction_reply(
        self,
        policy: UserReactionResponsePolicy,
        reaction: Reaction,
        persona: AiPersonaProfile,
    ) -> Result[str, ReactionTextPortError]:
        """ユーザー reaction に対する AI 返信本文を生成する。"""
