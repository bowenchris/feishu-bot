"""
飞书开放平台事件接收器
版本：v0.1.0 | 建立：2026-06-01
功能：接收飞书开放平台 Bot 的群消息事件，存储后供 AI 读取分析
"""

from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# 消息存储文件路径（Render 免费版用 /tmp 目录）
MSG_FILE = "/tmp/messages.json"

# 初始化文件（如果不存在就创建）
if not os.path.exists(MSG_FILE):
    with open(MSG_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)


# 飞书回调接口
@app.route("/feishu", methods=["POST"])
def feishu_webhook():
    data = request.get_json()

    # 处理飞书的 Challenge 验证
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # 收到消息，追加到文件里
    try:
        with open(MSG_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
        messages.append(data)
        with open(MSG_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        return jsonify({"code": 0, "msg": "success"})
    except Exception as e:
        return jsonify({"code": -1, "msg": str(e)}), 500


# 读取消息接口（我后面用这个地址读）
@app.route("/messages", methods=["GET"])
def get_messages():
    try:
        with open(MSG_FILE, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"code": -1, "msg": str(e)}), 500


# 健康检查
@app.route("/", methods=["GET"])
def health():
    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
