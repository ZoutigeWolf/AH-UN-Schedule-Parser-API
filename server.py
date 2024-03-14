import os
from datetime import datetime

from flask import Flask, request, jsonify

from textract import analyze

app = Flask(__name__)


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

    return jsonify(data), 200


if __name__ == "__main__":
    app.run(port=11111)
