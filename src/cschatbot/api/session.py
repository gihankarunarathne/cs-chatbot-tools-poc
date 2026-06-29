import uuid

_known_sessions: set[str] = set()


def new_session_id() -> str:
    sid = str(uuid.uuid4())
    _known_sessions.add(sid)
    return sid


def register_session(session_id: str) -> None:
    _known_sessions.add(session_id)


def list_sessions() -> list[str]:
    return list(_known_sessions)
