#!/usr/bin/env python3
"""Validate infrastructure claims against organizational policies.

This webhook validates PostgreSQL claims to ensure:
- Production-tier resources can only be created in production namespaces
- Staging-tier resources can be in staging or production namespaces
- Development-tier resources can be in any namespace
"""

from flask import Flask, request, jsonify
import json

app = Flask(__name__)

PRODUCTION_NAMESPACES = {"production", "prod", "prd"}
TIER_NAMESPACE_RULES = {
    "production": PRODUCTION_NAMESPACES,
    "staging": {"staging", "stg", "qa"} | PRODUCTION_NAMESPACES,
    "development": None  # Any namespace allowed
}

@app.route("/validate", methods=["POST"])
def validate():
    """Validate admission request against policies."""
    admission_review = request.get_json()
    req = admission_review["request"]

    obj = req["object"]
    namespace = req["namespace"]
    tier = obj.get("spec", {}).get("parameters", {}).get("tier", "development")

    allowed_namespaces = TIER_NAMESPACE_RULES.get(tier)

    if allowed_namespaces is not None and namespace not in allowed_namespaces:
        return jsonify({
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": req["uid"],
                "allowed": False,
                "status": {
                    "code": 403,
                    "message": f"Tier '{tier}' is not allowed in namespace '{namespace}'. "
                               f"Production resources must be in: {PRODUCTION_NAMESPACES}"
                }
            }
        })

    return jsonify({
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": req["uid"],
            "allowed": True
        }
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443, ssl_context="adhoc")
