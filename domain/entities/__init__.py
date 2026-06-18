from domain.entities.entity import Entity, EntityId

__all__ = ["Entity", "EntityId", "Lecture", "Reaction", "Utterance"]


def __getattr__(name: str):
    if name == "Lecture":
        from domain.entities.lecture import Lecture

        return Lecture
    if name == "Reaction":
        from domain.entities.reaction import Reaction

        return Reaction
    if name == "Utterance":
        from domain.entities.utterance import Utterance

        return Utterance
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
