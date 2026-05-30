import json
from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance
from domain.entities.reaction import Reaction
from domain.value_objects.formatted_lecture_log import FormattedLectureLog, LogFormat

class LectureLogFormatter:

    def format(
        self,
        lecture: Lecture,
        utterances: list[Utterance],
        reactions: list[Reaction],
        format_type: LogFormat
    ) -> FormattedLectureLog:
        self._validate_invariants(reactions)
        if format_type == LogFormat.MARKDOWN:
            log_content = self._to_markdown(lecture, utterances, reactions)
        elif format_type == LogFormat.JSON:
            log_content = self._to_json(lecture, utterances, reactions)
        else:
            raise ValueError(
                f"未対応のフォーマット形式が指定されました: {format_type}"
            )

        return FormattedLectureLog(format_type=format_type, content=log_content)

    def _validate_invariants(self, reactions: list[Reaction]) -> None:
        for reaction in reactions:
            if reaction.lecture_time_anchor is None:
                raise ValueError(
                    f"不変条件違反: Reaction(id={reaction.id}) の lecture_time_anchor が欠落しています"
                )
            if reaction.reply_target is None:
                raise ValueError(
                    f"不変条件違反: Reaction(id={reaction.id}) の reply_target が欠落しています"
                )

    def _to_markdown(
        self,
        lecture: Lecture,
        utterances: list[Utterance],
        reactions: list[Reaction]
    ) -> str:
        lines = [
            f"# 講義記録ログ: {lecture.title}",
            f"- 講義ID: {lecture.id}",
            f"- 開始位置: {lecture.started_at} ms / 終了位置: {lecture.ended_at} ms",
            "\n## タイムライン\n"
        ]

        timeline_items = []
        for u in utterances:
            timeline_items.append((u.time_range.start_ms, "utterance", u))
        for r in reactions:
            timeline_items.append((r.created_at, "reaction", r))

        timeline_items.sort(key=lambda item: item[0])

        for timestamp, item_type, item in timeline_items:
            if item_type == "utterance":
                lines.append(
                    f"### [{timestamp}ms] 講師: {item.speech_text.text}"
                )
            elif item_type == "reaction":
                role_label = item.speaker.role.upper()
                name = item.speaker.display_name
                target_kind = item.reply_target.reply_target_kind
                target_id = item.reply_target.reply_target_id
                
                lines.append(
                    f"  - **[{timestamp}ms] {role_label} ({name})**: {item.reaction_text.text} "
                    f"*(Reply to {target_kind}: {target_id})*"
                )

        return "\n".join(lines)

    def _to_json(
        self,
        lecture: Lecture,
        utterances: list[Utterance],
        reactions: list[Reaction]
    ) -> str:
        data = {
            "lecture": {
                "id": str(lecture.id),
                "title": lecture.title,
                "started_at": lecture.started_at,
                "ended_at": lecture.ended_at
            },
            "utterances": [
                {
                    "id": str(u.id),
                    "start_ms": u.time_range.start_ms,
                    "end_ms": u.time_range.end_ms,
                    "text": u.speech_text.text
                }
                for u in utterances
            ],
            "reactions": [
                {
                    "id": str(r.id),
                    "created_at": r.created_at,
                    "speaker": {
                        "role": r.speaker.role,
                        "display_name": r.speaker.display_name
                    },
                    "reply_target": {
                        "kind": r.reply_target.reply_target_kind,
                        "id": str(r.reply_target.reply_target_id)
                    },
                    "time_anchor": {
                        "start_ms": r.lecture_time_anchor.time_range.start_ms,
                        "end_ms": r.lecture_time_anchor.time_range.end_ms,
                        "utterance_id": str(r.lecture_time_anchor.utterance_id) if r.lecture_time_anchor.utterance_id else None
                    },
                    "text": r.reaction_text.text
                }
                for r in reactions
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
