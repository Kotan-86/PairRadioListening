from dataclasses import dataclass
from enum import Enum, auto
from domain.entities.entity import EntityId

class UserReactionIntent(Enum):
    TECHNICAL_QUESTION = auto()
    EMPATHY = auto()
    CONCERN = auto()
    OBSERVATION = auto()
    OTHER = auto()

class EmotionTone(Enum):
    POSITIVE = auto()
    NEUTRAL = auto()
    NEGATIVE = auto()
    CONFUSED = auto()

class AtmosphereLevel(Enum):
    QUIET = 1
    NORMAL = 2
    ACTIVE = 3
    ON_FIRE = 4

@dataclass(frozen=True)
class UserReactionAnalysisResult:
    intent: UserReactionIntent
    tone: EmotionTone

@dataclass(frozen=True)
class LecturerReactionPolicy:
    persona_id: EntityId
    summary_angle: str
    personalization_angle: str

@dataclass(frozen=True)
class UserReactionResponsePolicy:
    persona_id: EntityId
    tone: str
    response_intent: str
    reference_facts: list[str]
