#!/usr/bin/env python3
"""Serve plan-template.html with a plan, and hand the user's feedback back to the agent.

Usage (run it in the background, or as a blocking call with a long timeout):
    python plan_server.py <plan.json> [--port 8787] [--no-browser] [--out <file>]

- Serves the plan page on http://127.0.0.1:<port>/ (localhost only) and opens it.
- When the user presses "Send to agent", the page POSTs to /feedback. The server then
  prints ONE line, `PLAN_FEEDBACK {json}`, writes the same JSON to --out (default:
  plan-feedback.json next to plan.json), and exits with code 0.
- The agent reads that line (or the file) and acts on it. To show a revised plan, rewrite
  plan.json and run the server again; the user just reloads the tab.

Standard library only. The plan JSON format is documented at the top of plan-template.html.
"""
import argparse
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

TEMPLATE = Path(__file__).with_name("plan-template.html")
MAX_BODY = 1_000_000  # ponytail: plenty for plan feedback; reject anything bigger


def render(plan_path: Path) -> bytes:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    data = json.dumps(plan, indent=1).replace("</", "<\\/")  # can't close the <script> early
    html = TEMPLATE.read_text(encoding="utf-8")
    start = html.index('<script type="application/json" id="plan-data">')
    start = html.index(">", start) + 1
    end = html.index("</script>", start)
    return (html[:start] + "\n" + data + "\n" + html[end:]).encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", type=Path, help="plan JSON file")
    ap.add_argument("--port", type=int, default=8787, help="0 picks a free port")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    out = args.out or args.plan.with_name("plan-feedback.json")
    render(args.plan)  # fail fast on a bad plan file, before opening anything

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):  # keep stdout for the feedback line only
            pass

        def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                self._send(200, render(args.plan), "text/html; charset=utf-8")  # re-read: reload shows edits
            else:
                self._send(404)

        def do_POST(self):
            if self.path != "/feedback":
                return self._send(404)
            length = int(self.headers.get("Content-Length") or 0)
            if not 0 < length <= MAX_BODY:
                return self._send(413)
            try:
                feedback = json.loads(self.rfile.read(length))
            except ValueError:
                return self._send(400, b"invalid JSON")
            out.write_text(json.dumps(feedback, indent=2), encoding="utf-8")
            self._send(200, b"ok")
            print("PLAN_FEEDBACK " + json.dumps(feedback), flush=True)  # ASCII-safe on any console
            threading.Thread(target=server.shutdown, daemon=True).start()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"PLAN_URL {url}", file=sys.stderr, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
