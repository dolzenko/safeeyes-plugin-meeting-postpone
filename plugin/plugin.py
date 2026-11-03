import json
import logging

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread, Lock

context = None


def init(ctx, safeeyes_config, plugin_config) -> None:
    global context
    context = ctx
    context["plugin_config"] = plugin_config
    presence_manager = PresenceManager()
    context["presence_manager"] = presence_manager
    server_thread = Thread(
        target=run_server, args=(presence_manager,), daemon=True
    )
    server_thread.start()


def on_pre_break(break_obj) -> bool:
    """Lifecycle method executes before the pre-break period."""
    return _should_skip_break()


def on_start_break(break_obj) -> bool:
    """Lifecycle method executes just before the break."""
    return _should_skip_break()


def _should_skip_break() -> bool:
    presence = context["presence_manager"].get_status()
    if presence is None:
        return False
    # Normalize status: replace hyphens and spaces with underscores
    setting = f"presence_{presence.replace('-', '_').replace(' ', '_')}"
    if setting not in context["plugin_config"]:
        logging.warning(f"{presence} is not a valid presence status.")
        return False
    if context["plugin_config"][setting]:
        logging.info(f"Presence status is {presence}. Skipping break.")
        return True
    logging.info(f"Presence status is {presence}. Break allowed.")
    return False


def capturing_binaries(pactl_json: str) -> set[str]:
    return {
        binary
        for stream in json.loads(pactl_json)
        if (binary := stream["properties"].get("application.process.binary"))
    }


class PresenceManager:
    def __init__(self):
        self._status = None
        self._lock = Lock()

    def set_status(self, status):
        with self._lock:
            self._status = status

    def get_status(self):
        with self._lock:
            return self._status


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.presence_manager = kwargs.pop("presence_manager", None)
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.add_cors_headers()
        self.end_headers()

    def do_POST(self):
        self.add_cors_headers()
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode("utf-8")

        try:
            data = json.loads(body)
            if "status" in data:
                self.presence_manager.set_status(data["status"])
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_error(400, "Missing 'status' in JSON data")
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON data")

    def add_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_server(presence_manager: PresenceManager, port=6776):
    server_address = ("", port)

    def handler(*args, **kwargs):
        SimpleHTTPRequestHandler(*args, presence_manager=presence_manager, **kwargs)

    httpd = HTTPServer(server_address, handler)
    logging.info(f"Starting presence server on port {port}...")
    httpd.serve_forever()
