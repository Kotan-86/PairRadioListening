# 仕様: docs/spec/domain.md#reaction（集約ルート）
from dataclasses import dataclass

from domain.entities.entity import Entity, EntityId
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget


@dataclass(kw_only=True)
class Reaction(Entity):
    lecture_id: EntityId
    speaker: DialogueSpeaker
    reply_target: ReplyTarget
    lecture_time_anchor: LectureTimeAnchor
    reaction_text: ReactionText
    audio_data: AudioData
    created_at: int
