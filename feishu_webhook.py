"""
飞书开放平台事件接收器
版本：v0.1.0 | 建立：2026-06-01
功能：接收飞书开放平台 Bot 的群消息事件，存储后供 AI 读取分析

使用前提：
  1. 在 open.feishu.cn 创建应用，开启机器人能力
  2. 配置事件回调 URL 指向本服务
  3. 订阅 im.message.receive_v1 事件
"""

from flask import Flask, request, jsonify
import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 消息存储文件（存储在应用根目录）
MESSAGE_FILE = "feishu_messages.json"


def load_messages():
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_message(msg_type, content, sender=None, chat_id=None):
    messages = load_messages()
    entry = {
        "time": datetime.now().isoformat(),
        "type": msg_type,
        "content": content,
    }
    if sender:
        entry["sender"] = sender
    if chat_id:
        entry["chat_id"] = chat_id
    messages.append(entry)
    # 保留最近 2000 条
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(messages[-2000:], f, ensure_ascii=False, indent=2)
    logger.info(f"消息已存储: {content[:50]}")


@app.route("/", methods=["POST"])
def webhook():
    """飞书开放平台事件回调入口"""
    data = request.json
    raw = request.get_data(as_text=True)
    logger.info(f"收到请求: {raw[:500]}")

    if not data:
        return jsonify({"code": -1, "msg": "no data"})

    # 处理飞书 Challenge 验证
    if data.get("type") == "url_verification":
        challenge = data.get("challenge")
        logger.info("收到 Challenge 验证请求")
        return jsonify({"challenge": challenge})

    # 处理消息事件
    header = data.get("header", {})
    event_type = header.get("event_type", "")

    if event_type == "im.message.receive_v1":
        event = data.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})

        # 提取消息内容
        msg_type = message.get("message_type", "")
        content_raw = message.get("content", "{}")

        # 文本消息内容在 content 字段的 text 里
        try:
            content_obj = json.loads(content_raw)
            text = content_obj.get("text", content_raw)
        except (json.JSONDecodeError, TypeError):
            text = str(content_raw)

        # 提取发送者信息
        sender_info = {
            "id": sender.get("sender_id", {}).get("open_id", ""),
            "name": sender.get("sender_id", {}).get("union_id", ""),
        }

        chat_id = message.get("chat_id", "")

        save_message(
            msg_type=msg_type,
            content=text,
            sender=sender_info,
            chat_id=chat_id,
        )

        return jsonify({"code": 0})

    # 其他事件
    logger.info(f"收到未处理事件: {event_type}, header: {json.dumps(header)[:200]}")
    return jsonify({"code": 0})


@app.route("/messages", methods=["GET"])
def get_messages():
    """读取存储的消息（供 AI 查询）"""
    return jsonify(load_messages())


@app.route("/ping", methods=["GET"])
def ping():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
