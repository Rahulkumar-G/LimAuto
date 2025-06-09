from pathlib import Path
import json
import yaml
from flask import Flask, jsonify, request, Response

import importlib
from typing import Dict, Type

from .core import BookOrchestrator
from .utils.metrics import TokenMetricsTracker
from .agents.base import BaseAgent
from .monitoring import status_updates

app = Flask(__name__)

# Default config path within the package
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _discover_agents() -> Dict[str, Type[BaseAgent]]:
    """Dynamically discover available agent classes."""
    packages = [
        "BookLLM.src.agents.content",
        "BookLLM.src.agents.content.back_matter",
        "BookLLM.src.agents.content.front_matter",
        "BookLLM.src.agents.enhancement",
        "BookLLM.src.agents.review",
    ]
    registry: Dict[str, Type[BaseAgent]] = {}
    for pkg_name in packages:
        try:
            pkg = importlib.import_module(pkg_name)
            for name in getattr(pkg, "__all__", []):
                cls = getattr(pkg, name, None)
                if isinstance(cls, type):
                    registry[name] = cls
        except Exception:
            continue
    return registry


AGENT_REGISTRY = _discover_agents()


# Path for the metrics file determined from configuration
def _metrics_file_path() -> Path:
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
    output_dir = config.get("system", {}).get("output_dir", "./book_output")
    return Path(output_dir) / "final_token_metrics.json"


@app.route("/generate", methods=["POST"])
def generate_book():
    data = request.get_json(force=True)
    topic = data.get("topic")
    if not topic:
        return jsonify({"error": "'topic' field required"}), 400

    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}

    orchestrator = BookOrchestrator(config)
    orchestrator.generate_book(topic=topic)
    return jsonify({"message": "Book generation completed"})


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Return final token usage metrics."""
    metrics_file = _metrics_file_path()
    if not metrics_file.exists():
        return jsonify({"error": "metrics not found"}), 404

    with open(metrics_file) as f:
        data = json.load(f)

    tracker = TokenMetricsTracker()
    tracker.metrics = data
    return jsonify(tracker.get_summary())


@app.route("/api/agents", methods=["GET"])
def list_agents():
    """Return available agent names."""
    return jsonify(sorted(AGENT_REGISTRY.keys()))


@app.route("/api/dispatch", methods=["POST"])
def dispatch_prompt():
    """Send a prompt to a selected agent and return the response."""
    data = request.get_json(force=True)
    agent_name = data.get("agent")
    prompt = data.get("prompt", "").strip()
    if not agent_name or not prompt:
        return jsonify({"error": "'agent' and 'prompt' required"}), 400

    cls = AGENT_REGISTRY.get(agent_name)
    if not cls:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 400

    # For this lightweight API we simply echo the prompt rather than invoking
    # heavy LLM pipelines which require external dependencies.
    try:
        response = f"[{agent_name}] {prompt}"
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"response": response})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/events/agent-status")
def agent_status_events():
    def generate():
        while True:
            payload = status_updates.get()
            yield f"data: {json.dumps(payload)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
