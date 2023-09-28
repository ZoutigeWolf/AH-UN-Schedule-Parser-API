from flask import Flask, request, render_template, jsonify
import base64
from datetime import datetime
from threading import Thread
import os

from textract import analyze, load_json

app = Flask(__name__)


@app.get("/")
def home_view():
    return render_template("home.html")


@app.post("/")
def post_roster():
    image_b64 = request.json.get("image")
    print(image_b64)
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


@app.get("/schedule")
def get_schedule():
    year = request.args.get("year")

    if year is None:
        year = datetime.now().year

    year = str(year)

    week = request.args.get("week")

    if week is None:
        week = datetime.now().isocalendar().week

    week = str(week)

    per_person = request.args.get("pp") is not None

    schedule = load_json("schedule.json")

    if year not in schedule.keys():
        return "Year not found", 404

    if week not in schedule[year].keys():
        return "Week not found", 404

    schedule = schedule[year][week]

    if per_person:
        pp_schedule = {}
        for d, s in schedule.items():
            for p, t in s.items():
                if p not in pp_schedule.keys():
                    pp_schedule[p] = [t[0]]

                pp_schedule[p].append(t[1])

        schedule = pp_schedule

    return jsonify(schedule), 200


if __name__ == "__main__":
    app.run(port=11111)
