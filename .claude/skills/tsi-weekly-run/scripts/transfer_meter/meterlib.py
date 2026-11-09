"""Helpers: read the relay's counters, and an env that routes the DB through it."""

import os
import socket

from sqlalchemy.engine import make_url


def counters() -> tuple[int, int, int]:
    with socket.create_connection(("127.0.0.1", 5434)) as s:
        down, up, conns = s.makefile().readline().split()
    return int(down), int(up), int(conns)


def relay_env() -> dict[str, str]:
    """os.environ plus DATABASE_URL(_DIRECT) pointed at the relay (secrets never printed)."""
    import tsi  # noqa: F401
    from tsi.config import get_settings

    s = get_settings()
    env = dict(os.environ)
    for name in ("database_url", "database_url_direct"):
        v = getattr(s, name)
        v = v.get_secret_value() if hasattr(v, "get_secret_value") else str(v)
        url = make_url(v)
        assert url.host in ("localhost", "127.0.0.1"), "relay is for the local DB only"
        env[name.upper()] = url.set(port=5433).render_as_string(hide_password=False)
    return env


def mb(n: int) -> str:
    return f"{n / 1e6:.2f} MB"
