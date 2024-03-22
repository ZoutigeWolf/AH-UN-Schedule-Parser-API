import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from uuid import uuid4

from textract import analyze

app = Flask(__name__)

gunicorn_logger = logging.getLogger('gunicorn.debug')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


def load_json(file_name: str) -> dict | list:
    with open(file_name) as f:
        return json.load(f)


def write_json(file_name: str, data: dict | list) -> None:
    with open(file_name, 'w') as f:
        json.dump(data, f)


def get_user_from_token(token: str) -> dict | None:
    data = load_json("users.json")

    for user in data:
        if user.get("token") == token:
            return user

    return None


def save_user(user: dict) -> None:
    data = load_json("users.json")

    for i, u in enumerate(data):
        if user.get("token") == u.get("token"):
            del data[i]

    data.append(user)

    write_json("users.json", data)


def delete_user(token: str) -> None:
    data = load_json("users.json")

    for i, user in enumerate(data):
        if user.get("token") == token:
            del data[i]

    write_json("users.json", data)


@app.get("/users/<token>")
def get_user(token: str):
    user = get_user_from_token(token)

    if not user:
        return "User not found", 404

    return jsonify(user)


@app.get("/users")
def get_users():
    auth_token = request.headers.get("Authorization")

    auth_user = get_user_from_token(auth_token)

    if not auth_user or not auth_user.get("admin"):
        return jsonify([{k: v for k, v in u.items() if k != "token"} for u in load_json("users.json")])

    return jsonify(load_json("users.json"))


@app.post("/users")
def post_user():
    auth_token = request.headers.get("Authorization")

    auth_user = get_user_from_token(auth_token)

    if not auth_user:
        return "Unauthorized", 401

    if not auth_user.get("admin"):
        return "Forbidden", 403

    data = request.json

    name = data.get("name")
    admin = data.get("admin")

    if not name:
        return "Invalid data", 404

    user = {
        "name": name,
        "token": uuid4(),
        "admin": admin
    }

    save_user(user)

    return user, 201


@app.put("/users/<token>")
def put_user(token: str):
    auth_token = request.headers.get("Authorization")

    auth_user = get_user_from_token(auth_token)

    if not auth_user:
        return "Unauthorized", 401

    if not auth_user.get("admin"):
        return "Forbidden", 403

    user = get_user_from_token(token)

    if not user:
        return "User not found", 404

    data = request.json

    if data.keys() != ["name", "admin"]:
        return "Invalid data", 400

    data["token"] = token

    save_user(data)

    return data


@app.delete("/users/<token>")
def delete_user(token: str):
    auth_token = request.headers.get("Authorization")

    auth_user = get_user_from_token(auth_token)

    if not auth_user:
        return "Unauthorized", 401

    if not auth_user.get("admin"):
        return "Forbidden", 403

    user = get_user_from_token(token)

    if not user:
        return "User not found", 404

    delete_user(user.get("token"))

    return {
        "message": "User deleted"
    }


@app.post("/")
def post_roster():
    image = request.files.get('image')

    if not image:
        return "Missing image", 400

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    filename = f"{now}.jpeg"

    image.save(filename)

    data = analyze(filename)

    os.remove(filename)

    return jsonify(data)


if __name__ == "__main__":
    app.run(port=11111)
