# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from infrastructure.repositories.in_memory_lecture_repository import InMemoryLectureRepository
from domain.entities.lecture import Lecture
from domain.value_objects.ai_persona_profile import AiPersonaProfile


def test_in_memory_repository_save_and_find():
    repo = InMemoryLectureRepository()
    persona = AiPersonaProfile(
        id="p1",
        display_name="AI",
        persona_prompt="prompt",
    )
    lecture = Lecture(title="講義", persona_profiles=[persona])

    save_result = repo.save(lecture)
    assert save_result.is_ok()

    find_result = repo.find_by_id(str(lecture.id))
    assert find_result.is_ok()
    assert find_result.value is not None
    assert find_result.value.title == "講義"


def test_in_memory_repository_find_returns_none_when_missing():
    repo = InMemoryLectureRepository()

    find_result = repo.find_by_id("missing")

    assert find_result.is_ok()
    assert find_result.value is None
