# 仕様: docs/spec/framework_llm.md#3.3
from __future__ import annotations

import json

from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.dialogue_policies import UserReactionResponsePolicy
from domain.value_objects.lecture_llm_context import LectureLlmContext
from domain.value_objects.reply_target_focus import (
    ReactionReplyTargetFocus,
    ReplyTargetFocus,
    UtteranceReplyTargetFocus,
)


def _format_lecture_context(context: LectureLlmContext) -> str:
    if not context.utterance_excerpts:
        return "(講義コンテキストなし)"
    lines = []
    for excerpt in context.utterance_excerpts:
        lines.append(
            f"- [{excerpt.start_ms}-{excerpt.end_ms}ms] {excerpt.speech_text}"
        )
    return "\n".join(lines)


def _format_reply_target_focus(focus: ReplyTargetFocus) -> str:
    if isinstance(focus, UtteranceReplyTargetFocus):
        return (
            f"講師発話 ({focus.start_ms}-{focus.end_ms}ms): {focus.speech_text}"
        )
    if isinstance(focus, ReactionReplyTargetFocus):
        return (
            f"{focus.speaker_display_name}: {focus.reaction_text}"
        )
    raise ValueError(f"unknown reply_target_focus: {focus!r}")


def build_user_reaction_policy_prompt(
    *,
    persona_prompt: str,
    reaction_text: str,
    lecture_llm_context: LectureLlmContext,
    reply_target_focus: ReplyTargetFocus,
) -> str:
    return (
        "あなたは講義視聴中の学習パートナー AI です。次の入力から、"
        "ユーザー投稿への返信方針を JSON で返してください。\n\n"
        f"## ペルソナ\n{persona_prompt}\n\n"
        f"## 講義コンテキスト (anchor={lecture_llm_context.anchor_ms}ms)\n"
        f"{_format_lecture_context(lecture_llm_context)}\n\n"
        f"## 返信先\n{_format_reply_target_focus(reply_target_focus)}\n\n"
        f"## ユーザー投稿\n{reaction_text}\n\n"
        "出力 JSON キー: tone, response_intent, reference_facts (文字列配列)"
    )


def build_user_reaction_text_prompt(
    *,
    persona: AiPersonaProfile,
    policy: UserReactionResponsePolicy,
    reaction: Reaction,
    lecture_llm_context: LectureLlmContext,
    reply_target_focus: ReplyTargetFocus,
) -> str:
    policy_json = json.dumps(
        {
            "tone": policy.tone,
            "response_intent": policy.response_intent,
            "reference_facts": policy.reference_facts,
        },
        ensure_ascii=False,
    )
    return (
        "あなたは講義視聴中の学習パートナー AI です。方針に沿って短い壁打ち返信を"
        "日本語 1〜3 文で書いてください。JSON や前置きは不要です。\n\n"
        f"## ペルソナ ({persona.display_name})\n{persona.persona_prompt}\n\n"
        f"## 講義コンテキスト (anchor={lecture_llm_context.anchor_ms}ms)\n"
        f"{_format_lecture_context(lecture_llm_context)}\n\n"
        f"## 返信先\n{_format_reply_target_focus(reply_target_focus)}\n\n"
        f"## ユーザー投稿\n{reaction.reaction_text.text}\n\n"
        f"## 方針\n{policy_json}"
    )
