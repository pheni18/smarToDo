from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smartodo.db"
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    complete = db.Column(db.Boolean)


line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


class MethodPatterns:
    add = ["a", "add", "+", "あ"]
    get_list = ["l", "list"]
    delete = ["d", "delete", "x"]
    complete = ["c", "complete", "-"]
    update = ["u", "update", "う"]
    get = ["g", "get"]


def get_method(cmd):
    if cmd in MethodPatterns.add:
        return "add"
    elif cmd in MethodPatterns.get_list:
        return "get_list"
    elif cmd in MethodPatterns.delete:
        return "delete"
    elif cmd in MethodPatterns.complete:
        return "complete"
    elif cmd in MethodPatterns.update:
        return "update"
    elif cmd in MethodPatterns.get:
        return "get"
    else:
        return None


class Message:
    def __init__(self, text):
        self.method = get_method(text.split()[0])
        try:
            if self.method in ["add"]:
                self.id = None
                self.title = text.split()[1]
            elif self.method in ["get_list"]:
                self.id = None
                self.title = None
            elif self.method in ["delete", "complete", "get"]:
                self.id = int(text.split()[1])
                self.title = None
            elif self.method in ["update"]:
                self.id = int(text.split()[1])
                self.title = text.split()[2]
        except Exception:
            self.method = None
            self.id = None
            self.title = None


class ErrorMessages:
    VALID_ERROR = "有効な値を送信してください。"


@app.route('/', methods=['POST'])
def main():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "ok"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = Message(event.message.text)

    if message.method == "add":
        todo = Todo(title=message.title, complete=False)
        db.session.add(todo)
        db.session.commit()

        reply = ("add\n"
                 f"title: {message.title}")

    elif message.method == "get_list":
        incompletes = Todo.query.filter_by(complete=False).all()
        completes = Todo.query.filter_by(complete=True).all()

        reply = "incompletes:\n"
        for incomplete in incompletes:
            reply += f"id: {incomplete.id}, title: {incomplete.title}\n"

        reply += "complete:\n"
        for complete in completes:
            reply += f"id: {complete.id}, title: {complete.title}\n"

    elif message.method == "delete":
        todo = Todo.query.filter_by(id=message.id).first()
        db.session.delete(todo)
        db.session.commit()

        reply = ("delete\n"
                 f"title: {todo.title}")

    elif message.method == "complete":
        todo = Todo.query.filter_by(id=message.id).first()
        todo.complete = True
        db.session.commit()

        reply = ("complete\n"
                 f"title: {todo.title}")

    elif message.method == "update":
        todo = Todo.query.filter_by(id=message.id).first()
        todo.title = message.title
        db.session.commit()

        reply = ("update\n"
                 f"id: {todo.id}, title: {todo.title}")

    elif message.method == "get":
        todo = Todo.query.filter_by(id=message.id).first()

        reply = ("get\n"
                 f"id: {todo.id}, title: {todo.title}")

    else:
        reply = ErrorMessages.VALID_ERROR

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


if __name__ == '__main__':
    app.run()
