import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify

from textract import analyze


app = Flask(__name__)

gunicorn_logger = logging.getLogger('gunicorn.debug')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


@app.post("/")
def api_post_roster():
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
