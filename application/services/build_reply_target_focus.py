# 仕様: docs/spec/application.md#reply_target_focus, docs/spec/framework_llm.md#3.2
from domain.entities.lecture import Lecture
from domain.entities.reaction import Reaction
from domain.value_objects.reply_target_focus import (
    ReactionReplyTargetFocus,
    ReplyTargetFocus,
    UtteranceReplyTargetFocus,
)


def build_reply_target_focus(
    lecture: Lecture,
    user_reaction: Reaction,
    *,
    target_reaction: Reaction | None = None,
) -> ReplyTargetFocus | None:
    reply_target = user_reaction.reply_target
    if reply_target.reply_target_kind == "utterance":
        utterance = lecture.find_utterance_by_id(reply_target.reply_target_id)
        if utterance is None:
            return None
        return UtteranceReplyTargetFocus(
            kind="utterance",
            utterance_id=str(utterance.id),
            speech_text=utterance.speech_text.text,
            start_ms=utterance.time_range.start_ms,
            end_ms=utterance.time_range.end_ms,
        )

    if target_reaction is None:
        return None
    return ReactionReplyTargetFocus(
        kind="reaction",
        reaction_id=str(target_reaction.id),
        reaction_text=target_reaction.reaction_text.text,
        speaker_display_name=target_reaction.speaker.display_name,
    )
