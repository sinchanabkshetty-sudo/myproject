# aura/nlp.py
import re

def parse_command(text: str):
    """
    Return (intent, params) based on simple, robust patterns.
    Never return 3 values. This fixes the "not enough values to unpack" error.
    """
    if not text:
        return "unknown", {}

    t = text.lower().strip()

    # --- Open app / site ---
    # e.g., "open chrome", "open snipping tool", "open youtube"
    m = re.match(r"^(open|launch|start)\s+(.+)$", t)
    if m:
        target = m.group(2).strip()
        return "open_app", {"target": target}

    # --- Search web ---
    # e.g., "search for python decorators"
    if t.startswith("search for "):
        query = t.replace("search for ", "", 1).strip()
        return "search_web", {"query": query}

    # --- Media ---
    if t.startswith("play "):
        q = t.replace("play ", "", 1).strip()
        if "youtube" in t:
            q = q.replace("on youtube", "").strip()
            return "play_youtube", {"query": q}
        if "spotify" in t:
            q = q.replace("on spotify", "").strip()
            return "play_spotify", {"query": q}
        return "play_youtube", {"query": q}  # default to YouTube

    # --- Screenshot ---
    if "screenshot" in t or "take a screenshot" in t:
        return "screenshot", {}

    # --- System controls ---
    if "shutdown" in t:
        return "shutdown", {}
    if "restart" in t or "reboot" in t:
        return "restart", {}
    if "lock" in t or "lock pc" in t or "lock system" in t:
        return "lock", {}

    # Volume
    if "increase volume" in t or "volume up" in t:
        return "volume_up", {}
    if "decrease volume" in t or "volume down" in t:
        return "volume_down", {}
    if "mute" in t:
        return "volume_mute", {}

    # Brightness
    if "increase brightness" in t:
        return "brightness_up", {}
    if "decrease brightness" in t:
        return "brightness_down", {}

    # Connectivity
    if "wifi" in t or "wi-fi" in t:
        if "on" in t:  return "wifi_on", {}
        if "off" in t: return "wifi_off", {}
    if "bluetooth" in t:
        if "on" in t:  return "bt_on", {}
        if "off" in t: return "bt_off", {}

    # App reindex
    if "reindex apps" in t or "index apps" in t or "scan apps" in t:
        return "reindex_apps", {}

    return "unknown", {}
