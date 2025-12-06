# aura/skills/filesystem.py
import os, subprocess

def open_path(params=None):
    p = (params or {}).get("path","").strip().strip('"')
    if not p: return "Please provide a file or folder path."
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.abspath(p)
    if not os.path.exists(p):
        return "Path not found."
    os.startfile(p)
    return f"Opening {p}"

def list_dir(params=None):
    p = (params or {}).get("path","").strip() or "."
    p = os.path.abspath(os.path.expanduser(p))
    if not os.path.isdir(p):
        return "Folder not found."
    items = os.listdir(p)[:20]
    return "Items: " + ", ".join(items) if items else "Folder is empty."
