from flask import Flask, request
import base64
from datetime import datetime
from threading import Thread
import os

from textract import analyze

app = Flask(__name__)


@app.post("/")
def post_roster():
    image_b64 = request.json.get("image")

    if not image_b64:
        return "Missing image", 400

    image = base64.b64decode(image_b64)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not os.path.exists(f"data/{now}"):
        os.mkdir(f"data/{now}")

    filename = f"data/{now}/roster.jpeg"

    with open(filename, "wb") as f:
        f.write(image)

    t = Thread(target=analyze, args=[filename], daemon=True)
    t.start()

    return "Success", 200


if __name__ == "__main__":
    app.run(port=11111)
