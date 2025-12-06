# aura/engine.py
from aura import nlp

# Skills (import what you already have; all calls are wrapped in try/except)
from aura.skills import apps as apps_skill
from aura.skills import connectivity as conn_skill
from aura.skills import system_control as sys_skill
from aura.skills import websearch as web_skill

# ✅ Add this import at the top
from aura.database import save_command


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AttributeError:
        return "Feature not available on this system."
    except PermissionError:
        return "This action needs Administrator privileges. Run as admin and try again."
    except Exception as e:
        return f"Action failed: {e}"


def handle_command(text: str) -> str:
    """
    Main entry point called by your GUI. Returns a user-facing message string.
    """
    intent, params = nlp.parse_command(text)

    # Opening apps / websites (dynamic)
    if intent == "open_app":
        target = params.get("target", "")
        if not target:
            response = "Please specify what to open."
        else:
            response = _safe_call(apps_skill.open_application_any, target)

        save_command(text, response)  # ✅ Save history
        return response

    # Search the web
    if intent == "search_web":
        response = _safe_call(web_skill.search_web, params.get("query", ""))
        save_command(text, response)  # ✅ Save history
        return response

    # Media (handled via web search/links)
    if intent == "play_youtube":
        response = _safe_call(web_skill.play_youtube, params.get("query", ""))
        save_command(text, response)
        return response

    if intent == "play_spotify":
        response = _safe_call(web_skill.play_spotify, params.get("query", ""))
        save_command(text, response)
        return response

    # Screenshot
    if intent == "screenshot":
        response = _safe_call(sys_skill.take_screenshot)
        save_command(text, response)
        return response

    # System power/session
    if intent == "shutdown":
        response = _safe_call(sys_skill.shutdown_system)
        save_command(text, response)
        return response

    if intent == "restart":
        response = _safe_call(sys_skill.restart_system)
        save_command(text, response)
        return response

    if intent == "lock":
        response = _safe_call(sys_skill.lock_system)
        save_command(text, response)
        return response

    # Volume
    if intent == "volume_up":
        response = _safe_call(sys_skill.volume_up)
        save_command(text, response)
        return response

    if intent == "volume_down":
        response = _safe_call(sys_skill.volume_down)
        save_command(text, response)
        return response

    if intent == "volume_mute":
        response = _safe_call(sys_skill.volume_mute)
        save_command(text, response)
        return response

    # Brightness
    if intent == "brightness_up":
        response = _safe_call(sys_skill.brightness_up)
        save_command(text, response)
        return response

    if intent == "brightness_down":
        response = _safe_call(sys_skill.brightness_down)
        save_command(text, response)
        return response

    # Connectivity
    if intent == "wifi_on":
        response = _safe_call(conn_skill.toggle_wifi, True)
        save_command(text, response)
        return response

    if intent == "wifi_off":
        response = _safe_call(conn_skill.toggle_wifi, False)
        save_command(text, response)
        return response

    if intent == "bt_on":
        response = _safe_call(conn_skill.toggle_bluetooth, True)
        save_command(text, response)
        return response

    if intent == "bt_off":
        response = _safe_call(conn_skill.toggle_bluetooth, False)
        save_command(text, response)
        return response

    # App reindex
    if intent == "reindex_apps":
        response = _safe_call(apps_skill.index_apps)
        save_command(text, response)
        return response

    # --- NEW: defensive fallback so "open xyz" works even if NLP missed it ---
    low = text.strip().lower()
    if low.startswith("open "):
        target = low.replace("open ", "", 1).strip()
        if target:
            response = _safe_call(apps_skill.open_application_any, target)
            save_command(text, response)
            return response
    # -------------------------------------------------------------------------

    # Unknown
    response = ("Sorry, I didn’t understand that. Try: “open chrome”, "
                "“search for python interview questions”, “screenshot”, "
                "“increase volume”, or “wifi off”.")
    save_command(text, response)  # ✅ Final fallback logging
    return response
