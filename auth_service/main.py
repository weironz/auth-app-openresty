# main.py
from flask import Flask, request, jsonify
import uuid, time

app = Flask(__name__)
tokens = {}
TOKEN_TTL = 60

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"error": "missing username"}), 400

    token = str(uuid.uuid4())
    tokens[token] = {"username": username, "expires": time.time() + TOKEN_TTL}
    return jsonify({"token": token, "expires_in": TOKEN_TTL})

@app.route("/authen", methods=["GET"])
def authen():
    token = request.headers.get("X-Auth-Id")
    if not token:
        return jsonify({"allowed": False, "reason": "missing X-Auth-Id"}), 401

    token_info = tokens.get(token)
    if not token_info:
        return jsonify({"allowed": False, "reason": "invalid token"}), 403

    if time.time() > token_info["expires"]:
        return jsonify({"allowed": False, "reason": "expired"}), 403

    return jsonify({"allowed": True, "username": token_info["username"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
