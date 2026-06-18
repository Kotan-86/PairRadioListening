# MVP スコープ外: docs/spec/domain.md（timeline_atmosphere_assessor は post-MVP）
from domain.entities.utterance import Utterance
from domain.entities.reaction import Reaction
from domain.value_objects.dialogue_policies import AtmosphereLevel

class TimelineAtmosphereAssessor:

    def assess(self, recent_utterances: list[Utterance], recent_reactions: list[Reaction]) -> AtmosphereLevel:
        activity_score = self._calculate_activity_score(recent_utterances, recent_reactions)
        return self._determine_level(activity_score)

    def _calculate_activity_score(self, utterances: list[Utterance], reactions: list[Reaction]) -> float:
        utterance_weight = 1.0
        reaction_weight = 2.5
        return (len(utterances) * utterance_weight) + (len(reactions) * reaction_weight)

    def _determine_level(self, score: float) -> AtmosphereLevel:
        if score >= 15.0:
            return AtmosphereLevel.ON_FIRE
        elif score >= 8.0:
            return AtmosphereLevel.ACTIVE
        elif score >= 3.0:
            return AtmosphereLevel.NORMAL
        else:
            return AtmosphereLevel.QUIET
