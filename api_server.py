from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from router.task_router import route_task
from workflows.header_audit import audit_url_headers

DASHBOARD = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MuckBurg | SecOps Console</title>
    <style>
        :root { color-scheme: dark; --bg: #101413; --surface: #181e1c; --border: #343d39; --text: #edf2eb; --muted: #9daaa1; --accent: #b7e986; }
        * { box-sizing: border-box; }
        body { margin: 0; min-height: 100vh; color: var(--text); background: repeating-linear-gradient(90deg, transparent 0, transparent 79px, #ffffff05 80px), var(--bg); font-family: "Segoe UI", sans-serif; }
        header { border-bottom: 1px solid var(--border); background: #101413; }
        .topbar { max-width: 1200px; margin: auto; min-height: 68px; padding: 0 28px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
        .brand { display: flex; align-items: center; gap: 12px; font-size: 15px; font-weight: 700; }
        .brand-mark { width: 31px; height: 31px; display: grid; place-items: center; color: #101413; background: var(--accent); font-family: Georgia, serif; font-weight: 700; }
        .label { color: var(--muted); font: 11px/1.4 Consolas, monospace; text-transform: uppercase; }
        .status { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
        .dot { width: 7px; height: 7px; background: var(--accent); border-radius: 50%; }
        main { max-width: 1200px; margin: auto; padding: 55px 28px 80px; }
        .heading { display: flex; align-items: end; justify-content: space-between; gap: 24px; padding-bottom: 28px; border-bottom: 1px solid var(--border); }
        h1 { margin: 10px 0 0; font: 42px/1.1 Georgia, serif; font-weight: 400; }
        .layout { display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr); gap: 46px; padding-top: 32px; }
        .section-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
        .number { color: var(--accent); font: 12px Consolas, monospace; }
        h2 { margin: 0; font-size: 15px; font-weight: 600; }
        form { padding: 0 0 30px; margin-bottom: 28px; border-bottom: 1px solid var(--border); }
        label { display: block; margin-bottom: 10px; font-size: 13px; font-weight: 600; }
        input, textarea { width: 100%; padding: 13px 14px; border: 1px solid #49534d; border-radius: 2px; background: #101513; color: var(--text); font: 14px/1.5 Consolas, monospace; }
        input:focus, textarea:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
        textarea { min-height: 126px; resize: vertical; }
        input::placeholder, textarea::placeholder { color: #758178; }
        button { margin-top: 14px; padding: 11px 17px; border: 1px solid var(--accent); border-radius: 2px; background: var(--accent); color: #142012; font: 600 13px "Segoe UI", sans-serif; cursor: pointer; }
        button:hover { background: #d3f5b2; }
        button:disabled { opacity: .5; cursor: wait; }
        .secondary { color: var(--text); background: transparent; border-color: #68756c; }
        .secondary:hover { background: #28332d; }
        .output-header { display: flex; align-items: center; justify-content: space-between; gap: 15px; margin-bottom: 24px; }
        .output-header .section-heading { margin: 0; }
        #state { color: var(--accent); }
        #output { margin: 0; min-height: 350px; padding: 22px; border: 1px solid var(--border); background: var(--surface); color: #d9e3da; font: 13px/1.75 Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
        @media (max-width: 700px) { .topbar { padding: 0 20px; } main { padding: 40px 20px 60px; } h1 { font-size: 34px; } .heading { align-items: start; flex-direction: column; } .layout { grid-template-columns: 1fr; gap: 12px; } #output { min-height: 240px; } }
    </style>
</head>
<body>
    <header><div class="topbar"><div class="brand"><span class="brand-mark">M</span><span>MuckBurg</span></div><div class="status label"><span class="dot"></span>SecOps console</div></div></header>
    <main>
        <div class="heading"><div><div class="label">Workspace / Operations</div><h1>Security console</h1></div><div class="label">Local analysis</div></div>
        <div class="layout">
            <section aria-labelledby="operations-title">
                <div class="section-heading"><span class="number">01</span><h2 id="operations-title">New request</h2></div>
                <form id="audit-form"><label for="url">Target URL</label><input id="url" name="url" type="url" placeholder="https://example.com" required><button type="submit">Run header audit</button></form>
                <form id="ask-form"><label for="prompt">SecOps prompt</label><textarea id="prompt" name="prompt" placeholder="Ask a security question..." required></textarea><button type="submit" class="secondary">Submit prompt</button></form>
            </section>
            <section aria-labelledby="output-title">
                <div class="output-header"><div class="section-heading"><span class="number">02</span><h2 id="output-title">Output</h2></div><span id="state" class="label" role="status">Ready</span></div>
                <pre id="output" aria-live="polite">No output yet.</pre>
            </section>
        </div>
    </main>
    <script>
        const output = document.getElementById('output');
        const state = document.getElementById('state');
        const buttons = document.querySelectorAll('button[type="submit"]');
        async function submitRequest(endpoint, payload) {
            buttons.forEach(button => button.disabled = true);
            state.textContent = 'Running';
            output.textContent = 'Waiting for response...';
            try {
                const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const result = await response.json();
                if (!response.ok || result.error) throw new Error(result.error || `HTTP ${response.status}`);
                output.textContent = result.output || 'No output returned.';
                state.textContent = 'Complete';
            } catch (error) {
                output.textContent = `Request failed: ${error.message}`;
                state.textContent = 'Error';
            } finally {
                buttons.forEach(button => button.disabled = false);
            }
        }
        document.getElementById('audit-form').addEventListener('submit', event => { event.preventDefault(); submitRequest('/audit', { url: document.getElementById('url').value, heavy: false }); });
        document.getElementById('ask-form').addEventListener('submit', event => { event.preventDefault(); submitRequest('/ask', { prompt: document.getElementById('prompt').value, heavy: false }); });
    </script>
</body>
</html>"""

class MuckBurgHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        response = DASHBOARD.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        complexity = "high" if data.get("heavy") else "low"

        if self.path == "/audit":
            target = data.get("url", "https://example.com")
            result = audit_url_headers(target, complexity=complexity)
        elif self.path == "/ask":
            prompt = data.get("prompt", "")
            result = route_task(prompt, complexity=complexity)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Unknown endpoint. Use /audit or /ask"}')
            return

        response = json.dumps({"status": "ok", "output": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), MuckBurgHandler)
    print("[MuckBurg API] Listening on http://0.0.0 (Endpoints: /audit, /ask)")
    server.serve_forever()
