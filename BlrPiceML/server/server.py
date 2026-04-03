from __future__ import annotations

import json
import os
import pickle
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, make_response, request, send_from_directory

try:
    # When imported as `server.server`
    from . import util  # type: ignore
except ImportError:
    # When run as `python server/server.py`
    import util  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
CLIENT_DIR = BASE_DIR.parent / "client"

app = Flask(__name__)

MODEL_PATH = ARTIFACTS_DIR / "banglore_home_prices_model.pickle"
COLUMNS_PATH = ARTIFACTS_DIR / "columns.json"


def _cors(resp):
    # Basic CORS support for browser clients.
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp


def _truncate(items: list[str], limit: int = 15) -> list[str]:
    if len(items) <= limit:
        return items
    return items[:limit] + ["..."]


# Load ML artifacts once at startup.
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

DATA_COLUMNS: list[str] = util.DATA_COLUMNS
MODEL_FEATURE_COUNT = int(getattr(model, "n_features_in_", len(DATA_COLUMNS)))
ACTIVE_COLUMNS = DATA_COLUMNS[:MODEL_FEATURE_COUNT]
FEATURE_INDEX = {name: i for i, name in enumerate(ACTIVE_COLUMNS)}


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(CLIENT_DIR, "index.html")


@app.route("/<path:path>", methods=["GET"])
def static_files(path: str):
    file_path = CLIENT_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(CLIENT_DIR, path)
    resp = jsonify({"error": "Not found"})
    resp.status_code = 404
    return _cors(resp)


@app.route("/health", methods=["GET"])
def health():
    return _cors(
        jsonify(
            {
                "message": "Home Price Prediction API is running",
                "endpoints": {
                    "GET /get_location_names": "List supported locations",
                    "POST /predict_home_price": "Predict price using JSON body: location,total_sqft,bath,bhk",
                },
            }
        )
    )


@app.route("/get_location_names", methods=["GET", "OPTIONS"])
def get_location_names():
    if request.method == "OPTIONS":
        return _cors(make_response("", 204))

    locations = [c for c in ACTIVE_COLUMNS if c not in util.NUMERIC_FEATURES]
    return _cors(jsonify({"locations": locations}))


@app.route("/predict_home_price", methods=["POST", "OPTIONS"])
def predict_home_price():
    if request.method == "OPTIONS":
        return _cors(make_response("", 204))

    data = request.get_json(silent=True) or {}

    try:
        location = str(data.get("location", "")).strip().lower()
        total_sqft = float(data.get("total_sqft"))
        bath = float(data.get("bath"))
        bhk = float(data.get("bhk"))
    except (TypeError, ValueError):
        resp = jsonify({"error": "Invalid input. Provide JSON: location,total_sqft,bath,bhk"})
        resp.status_code = 400
        return _cors(resp)

    if not location:
        resp = jsonify({"error": "location is required"})
        resp.status_code = 400
        return _cors(resp)

    if location not in FEATURE_INDEX:
        locations = [c for c in ACTIVE_COLUMNS if c not in util.NUMERIC_FEATURES]
        resp = jsonify(
            {
                "error": (
                    f"Unknown location '{location}'. "
                    "If this location was added recently, retrain and export a new model."
                ),
                "valid_locations": _truncate(locations),
            }
        )
        resp.status_code = 400
        return _cors(resp)

    # Create the one-hot encoded feature vector.
    x_input = np.zeros(MODEL_FEATURE_COUNT, dtype=float)
    x_input[FEATURE_INDEX["total_sqft"]] = total_sqft
    x_input[FEATURE_INDEX["bath"]] = bath
    x_input[FEATURE_INDEX["bhk"]] = bhk
    x_input[FEATURE_INDEX[location]] = 1.0

    predicted_price = float(model.predict([x_input])[0])
    return _cors(jsonify({"predicted_price": predicted_price}))


if __name__ == "__main__":
    print("Starting Python Flask Server For Home Price Prediction...")
    # Change host/port if your front-end expects something else.
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
