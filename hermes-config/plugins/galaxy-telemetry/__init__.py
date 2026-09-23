"""
galaxy-telemetry plugin
Posts real-time skill activation signals to the Galaxy View server (port 8899).
Hook: on_skill_lifecycle
"""

from __future__ import annotations

import logging
import threading
import urllib.request
import json

logger = logging.getLogger(__name__)

GALAXY_URL = "http://172.20.0.1:8899/api/activate"
DEACTIVATE_URL = "http://172.20.0.1:8899/api/deactivate"

# Track active skills with a deactivation timer
_active_timers: dict[str, threading.Timer] = {}
_lock = threading.Lock()

# Timeout: how long after last "loaded" event until we consider skill inactive
DEACTIVATE_DELAY_S = 20.0


def _post(url: str, payload: dict) -> None:
    """Fire-and-forget HTTP POST; never blocks the main thread."""
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            logger.debug("galaxy-telemetry: %s -> %s", url, resp.status)
    except Exception as e:
        logger.debug("galaxy-telemetry: POST failed: %s", e)


def _fire(url: str, payload: dict) -> None:
    """Run _post in a daemon thread so it never blocks."""
    t = threading.Thread(target=_post, args=(url, payload), daemon=True)
    t.start()


def _schedule_deactivation(skill_name: str) -> None:
    """Cancel any pending deactivation, start a new one."""
    with _lock:
        old = _active_timers.pop(skill_name, None)
        if old:
            old.cancel()

        def _deactivate():
            with _lock:
                _active_timers.pop(skill_name, None)
            _fire(DEACTIVATE_URL, {"skill": skill_name})
            logger.debug("galaxy-telemetry: deactivated %s", skill_name)

        timer = threading.Timer(DEACTIVATE_DELAY_S, _deactivate)
        timer.daemon = True
        timer.start()
        _active_timers[skill_name] = timer


def on_skill_lifecycle(**kwargs) -> None:
    """
    Called by Hermes whenever a skill lifecycle event fires.
    kwargs includes: action, skill_name, provenance, task_id, session_id, use_count, etc.
    """
    action = kwargs.get("action", "")
    skill_name = kwargs.get("skill_name", "")

    if not skill_name:
        return

    if action == "loaded":
        # Skill is being actively used — activate in galaxy view
        _fire(GALAXY_URL, {"skill": skill_name})
        logger.debug("galaxy-telemetry: activated %s (action=%s)", skill_name, action)
        # Schedule auto-deactivation after 20s of no further "loaded" events
        _schedule_deactivation(skill_name)

    elif action in ("archived", "stale"):
        # Not really "active use" but let's ignore these for the visualizer
        pass


def register(ctx) -> None:
    ctx.register_hook("on_skill_lifecycle", on_skill_lifecycle)
    logger.info("galaxy-telemetry plugin registered — posting to %s", GALAXY_URL)
