from pathlib import Path

import yaml
from flask import Flask, jsonify, request

from .core import BookOrchestrator

app = Flask(__name__)

# Default config path within the package
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


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


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
