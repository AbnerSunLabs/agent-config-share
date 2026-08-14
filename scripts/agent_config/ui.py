"""本机 HTTP 面板：只绑定 127.0.0.1，同步逻辑走现有 sync。"""

from __future__ import annotations

import errno
import json
import mimetypes
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from agent_config import sync, ui_catalog
from agent_config.schema import HOSTS, SchemaError

BIND_HOST = "127.0.0.1"
STATIC_DIR = Path(__file__).resolve().parent / "ui_static"


def _json(status: int, payload: dict[str, Any]) -> tuple[int, str, bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return status, "application/json; charset=utf-8", body


def _parse_hosts(raw: Any) -> list[str] | None:
    if raw is None or raw == []:
        return list(HOSTS)
    if not isinstance(raw, list):
        return None
    hosts: list[str] = []
    for item in raw:
        if item not in HOSTS:
            return None
        if item not in hosts:
            hosts.append(item)
    return hosts or list(HOSTS)


def _parse_only(raw: Any) -> str | None | object:
    if raw is None:
        return None
    if raw in ("mcp", "hooks"):
        return raw
    return object()


def _schema_error(_exc: SchemaError) -> tuple[int, str, bytes]:
    return _json(400, {"error": "schema", "message": "清单无效"})


def _inventory() -> Any:
    try:
        return sync.load_inventory(), None
    except SchemaError as exc:
        return None, _schema_error(exc)


def handle_catalog() -> tuple[int, str, bytes]:
    loaded, err = _inventory()
    if err is not None:
        return err
    mcp_entries, hook_entries = loaded
    return _json(200, ui_catalog.build_catalog(mcp_entries, hook_entries))


def handle_check(payload: dict[str, Any]) -> tuple[int, str, bytes]:
    hosts = _parse_hosts(payload.get("hosts"))
    if hosts is None:
        return _json(400, {"error": "bad_hosts", "message": "宿主非法"})
    only = _parse_only(payload.get("only"))
    if only is not None and only not in ("mcp", "hooks"):
        return _json(400, {"error": "bad_only", "message": "only 非法"})
    loaded, err = _inventory()
    if err is not None:
        return err
    mcp_entries, hook_entries = loaded
    only_arg: str | None = only if only in ("mcp", "hooks") else None
    catalog = ui_catalog.build_catalog(mcp_entries, hook_entries)
    ui_catalog.annotate_status(catalog, mcp_entries, hook_entries, hosts, only_arg)
    return _json(200, catalog)


def handle_apply(payload: dict[str, Any]) -> tuple[int, str, bytes]:
    if payload.get("confirm") is not True:
        return _json(400, {"error": "confirm_required"})
    hosts = _parse_hosts(payload.get("hosts"))
    if hosts is None:
        return _json(400, {"error": "bad_hosts", "message": "宿主非法"})
    only = _parse_only(payload.get("only"))
    if only is not None and only not in ("mcp", "hooks"):
        return _json(400, {"error": "bad_only", "message": "only 非法"})
    only_arg: str | None = only if only in ("mcp", "hooks") else None
    loaded, err = _inventory()
    if err is not None:
        return err
    mcp_entries, hook_entries = loaded
    try:
        target_paths = sync.collect_apply_paths(only_arg, hosts=hosts)
        sync.backup_files(target_paths)
        sync.apply(
            mcp_entries,
            hook_entries,
            only=only_arg,
            prune=False,
            hosts=hosts,
        )
    except Exception as exc:  # noqa: BLE001 — 面板不能伪装成功
        return _json(500, {"error": "apply_failed", "message": type(exc).__name__})
    catalog = ui_catalog.build_catalog(mcp_entries, hook_entries)
    ui_catalog.annotate_status(catalog, mcp_entries, hook_entries, hosts, only_arg)
    return _json(200, catalog)


def handle_skills_open(payload: dict[str, Any]) -> tuple[int, str, bytes]:
    raw_path = payload.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        return _json(400, {"error": "bad_path", "message": "路径非法"})
    wanted = Path(raw_path).resolve()
    allowed = {Path(card["path"]).resolve() for card in ui_catalog.scan_skills()}
    if wanted not in allowed:
        return _json(400, {"error": "not_allowed", "message": "路径不在 Skills 白名单"})
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.run([opener, str(wanted)], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        return _json(500, {"error": "open_failed", "message": "打开目录失败"})
    return _json(200, {"error": None, "ok": True})


def handle_static(rel: str) -> tuple[int, str, bytes] | None:
    if ".." in Path(rel).parts:
        return 403, "text/plain; charset=utf-8", b"forbidden"
    target = (STATIC_DIR / rel).resolve()
    try:
        target.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return 403, "text/plain; charset=utf-8", b"forbidden"
    if not target.is_file():
        return None
    mime, _ = mimetypes.guess_type(str(target))
    data = target.read_bytes()
    return 200, mime or "application/octet-stream", data


def dispatch(method: str, path: str, body: bytes = b"") -> tuple[int, str, bytes]:
    """供测试与 HTTP Handler 共用的路由。"""
    parsed = urlparse(path)
    route = unquote(parsed.path)
    if method == "GET" and route == "/":
        static = handle_static("index.html")
        if static is None:
            return 500, "text/plain; charset=utf-8", b"missing index.html"
        return static
    if method == "GET" and route.startswith("/static/"):
        static = handle_static(route[len("/static/") :])
        if static is None:
            return 404, "text/plain; charset=utf-8", b"not found"
        return static
    if method == "GET" and route == "/api/catalog":
        return handle_catalog()
    if method in {"POST"} and route in {
        "/api/check",
        "/api/apply",
        "/api/skills/open",
    }:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _json(400, {"error": "bad_json", "message": "JSON 无效"})
        if not isinstance(payload, dict):
            return _json(400, {"error": "bad_json", "message": "JSON 必须是对象"})
        if route == "/api/check":
            return handle_check(payload)
        if route == "/api/apply":
            return handle_apply(payload)
        return handle_skills_open(payload)
    return 404, "text/plain; charset=utf-8", b"not found"


class UiHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _write(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        status, content_type, body = dispatch("GET", self.path)
        self._write(status, content_type, body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b""
        status, content_type, body = dispatch("POST", self.path, raw)
        self._write(status, content_type, body)


def serve(port: int, open_browser: bool) -> int:
    try:
        httpd = HTTPServer((BIND_HOST, port), UiHandler)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            print(f"端口占用: {port}，请换 --port", file=sys.stderr)
        else:
            print(f"无法监听 {BIND_HOST}:{port}: {exc}", file=sys.stderr)
        return 2
    url = f"http://{BIND_HOST}:{port}/"
    print(url)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0
