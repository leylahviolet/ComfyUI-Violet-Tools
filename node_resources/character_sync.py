# -*- coding: utf-8 -*-
"""
Violet Tools — Character backend (wireless-only)

Purpose (2.0+): Provide REST endpoints to list/save/delete character profiles
for the Character Curator UI. All node-level character wiring and automatic UI
sync have been removed in favor of a wireless flow.

Non-invasive: If anything fails, it quietly does nothing. No schema changes.
"""

import json
import os
from typing import Dict, Any, List

try:
    import server  # type: ignore  # ComfyUI's server module
except (ImportError, AttributeError):  # pragma: no cover - ComfyUI only
    server = None  # type: ignore

# No package-relative imports to keep analyzers happy; replicate minimal path resolver


def _get_characters_folder() -> str:
    """Preferred characters directory under ComfyUI user dir, with fallback."""
    try:
        import importlib
        folder_paths = importlib.import_module("folder_paths")  # type: ignore
        # Try user directory first
        user_dir = getattr(folder_paths, "get_user_directory", None)
        if callable(user_dir):
            base_user = user_dir()
        else:
            out_dir = folder_paths.get_output_directory()
            base_user = os.path.join(os.path.dirname(str(out_dir)), "user")
        preferred = os.path.join(str(base_user), "default", "comfyui-violet-tools", "characters")
        return preferred
    except (ImportError, AttributeError, OSError, TypeError):  # pragma: no cover - defensive
        return os.path.join(os.getcwd(), "user", "default", "comfyui-violet-tools", "characters")


def _sanitize_filename(s: str) -> str:
    invalid = '<>:"/\\|?*'
    trans = str.maketrans({c: '_' for c in invalid})
    s2 = (s or "").translate(trans)
    s2 = ' '.join(s2.split())
    s2 = s2.strip('. ')
    return s2 or "character"


def _list_character_names() -> List[str]:
    """List saved character file stems from the preferred user folder only.

    Returns a sorted list of character names (without .json extension).
    Non-fatal on errors; returns empty list on failure.
    """
    names: set[str] = set()
    try:
        import importlib
        folder_paths = importlib.import_module("folder_paths")  # type: ignore
    # Preferred user path ONLY (drop legacy output/characters)
        user_dir = getattr(folder_paths, "get_user_directory", None)
        if callable(user_dir):
            base_user = user_dir()
        else:
            out_dir = folder_paths.get_output_directory()
            base_user = os.path.join(os.path.dirname(str(out_dir)), "user")
        preferred = os.path.join(str(base_user), "default", "comfyui-violet-tools", "characters")
        if os.path.isdir(preferred):
            try:
                for f in os.listdir(preferred):
                    if f.endswith(".json"):
                        names.add(f[:-5])
            except OSError:
                pass
    except (ImportError, AttributeError, OSError, TypeError):
        # Attempt cwd fallback used by _get_characters_folder
        base = os.path.join(os.getcwd(), "user", "default", "comfyui-violet-tools", "characters")
        if os.path.isdir(base):
            try:
                for f in os.listdir(base):
                    if f.endswith(".json"):
                        names.add(f[:-5])
            except OSError:
                pass
    return sorted(names)


def _load_character_payload(name: str) -> Dict[str, Any]:
    """Load character JSON by name. Returns dict or {} on failure."""
    if not name:
        return {}
    folder = _get_characters_folder()
    path = os.path.join(folder, f"{_sanitize_filename(name)}.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError, TypeError):
        return {}
    return {}


# 2.0+: Prompt auto-sync removed. No-op placeholders kept for clarity.


def _broadcast_update(_: Dict[str, Dict[str, Any]]):
    return


def _find_selected_character(_: Dict[str, Any]) -> str:
    return ""


def _onprompt(json_data: Dict[str, Any]):
    # 2.0+: No prompt-time UI sync; return input unchanged
    return json_data


def _register():  # pragma: no cover
    if server is None:
        return
    # 2.0+: No on-prompt sync registration
    # Register minimal fetch endpoint without global aiohttp import
    try:
        # Lazy import here to avoid editor/type checker noise
        from aiohttp import web as _web  # type: ignore

        @server.PromptServer.instance.routes.get("/violet/character")
        def get_character(request):  # type: ignore
            # If list is requested or no name provided, return list of saved characters
            query = request.rel_url.query
            name = query.get("name", "")
            want_list = query.get("list", "0") in ("1", "true", "yes") or not name
            if want_list:
                return _web.json_response({"names": _list_character_names()})
            data = _load_character_payload(name)
            if data:
                return _web.json_response(data)
            return _web.Response(text="Not found", status=404)

        @server.PromptServer.instance.routes.post("/violet/character")
        async def save_character(request):  # type: ignore
            try:
                body = await request.json()
            except (TypeError, ValueError):
                return _web.Response(text="Invalid JSON", status=400)

            if not isinstance(body, dict):
                return _web.Response(text="Invalid payload", status=400)

            name = body.get("name", "")
            data = body.get("data", {})
            if not isinstance(name, str) or not name.strip():
                return _web.Response(text="Missing name", status=400)
            if not isinstance(data, dict):
                return _web.Response(text="Invalid data", status=400)

            folder = _get_characters_folder()
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError:
                return _web.Response(text="Failed to create folder", status=500)

            file_stem = _sanitize_filename(name.strip())
            file_path = os.path.join(folder, f"{file_stem}.json")
            payload = {
                "name": name.strip(),
                "created": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
                "violet_tools_version": "2.0.0",
                "data": data,
            }
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
                return _web.json_response({"ok": True, "path": file_path})
            except OSError as e:
                return _web.Response(text=f"Save failed: {e}", status=500)

        @server.PromptServer.instance.routes.delete("/violet/character")
        async def delete_character(request):  # type: ignore
            name = request.rel_url.query.get("name", "")
            if not name:
                return _web.Response(text="Missing name", status=400)
            file_stem = _sanitize_filename(name)
            folder = _get_characters_folder()
            path = os.path.join(folder, f"{file_stem}.json")
            if not os.path.exists(path):
                return _web.Response(text="Not found", status=404)
            try:
                os.remove(path)
                return _web.json_response({"ok": True})
            except OSError as e:
                return _web.Response(text=f"Delete failed: {e}", status=500)
    except (ImportError, AttributeError):
        # Endpoint unavailable; UI buttons will be no-op without it
        pass


_register()
