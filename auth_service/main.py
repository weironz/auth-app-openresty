# main.py
from flask import Flask, request, jsonify
import uuid, time

app = Flask(__name__)

# 用一个简单的 dict 做内存存储（生产环境当然要用 Redis/数据库）
tokens = {}

# token 有效期，秒
TOKEN_TTL = 60

@app.route("/login", methods=["POST"])
def login():
    """
    模拟登录：只要传了 username，就给一个 token
    """
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"error": "missing username"}), 400

    # 随机生成 token
    token = str(uuid.uuid4())
    tokens[token] = {
        "username": username,
        "expires": time.time() + TOKEN_TTL
    }

    return jsonify({"token": token, "expires_in": TOKEN_TTL})

@app.route("/authen", methods=["GET"])
def authen():
    """
    鉴权接口：Nginx/OpenResty 调用这里来确认 token 是否有效
    """
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
