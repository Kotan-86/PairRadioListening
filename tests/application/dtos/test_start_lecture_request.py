# 仕様: docs/spec/application.md#StartLectureRequest
from application.dtos.start_lecture_request import StartLectureRequest
from application.errors import InvalidPersonaProfiles


def test_start_lecture_request_validate_fails_when_persona_profiles_empty():
    request = StartLectureRequest.from_fields(persona_profiles=[])

    result = request.validate()

    assert result.is_err()
    assert isinstance(result.error, InvalidPersonaProfiles)


def test_start_lecture_request_validate_fails_when_persona_profiles_more_than_one():
    from domain.value_objects.ai_persona_profile import AiPersonaProfile

    personas = [
        AiPersonaProfile(id="p1", display_name="AI1", persona_prompt="prompt1"),
        AiPersonaProfile(id="p2", display_name="AI2", persona_prompt="prompt2"),
    ]
    request = StartLectureRequest.from_fields(persona_profiles=personas)

    result = request.validate()

    assert result.is_err()
    assert isinstance(result.error, InvalidPersonaProfiles)


def test_start_lecture_request_validate_succeeds_with_one_persona():
    from domain.value_objects.ai_persona_profile import AiPersonaProfile

    persona = AiPersonaProfile(
        id="p1",
        display_name="AI",
        persona_prompt="prompt",
    )
    request = StartLectureRequest.from_fields(persona_profiles=[persona])

    result = request.validate()

    assert result.is_ok()
