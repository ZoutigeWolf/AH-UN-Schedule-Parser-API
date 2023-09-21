import os
from datetime import datetime, timedelta
import cv2
import boto3
import csv
import requests
import json

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    scores = []
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map[child_id]
                if cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        # create new row
                        rows[row_index] = {}

                    # get confidence score
                    scores.append(str(cell['Confidence']))

                    # get the text value
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows, scores


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        if "," in word['Text'] and word['Text'].replace(",", "").isnumeric():
                            text += '"' + word['Text'] + '"' + ' '
                        else:
                            text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '
    return text


def get_table_csv_results(file_name):
    img = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
    (thresh, im_bw) = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    cv2.imwrite("temp.png", im_bw)
    with open("temp.png", 'rb') as file:
        img_test = file.read()
        bytes_test = bytearray(img_test)
        print('Image loaded', file_name)

    os.remove("temp.png")

    # process using image bytes
    # get the results
    session = boto3.Session(profile_name='default')
    client = session.client('textract', region_name='eu-west-2')
    response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['TABLES'])

    # Get the text blocks
    blocks = response['Blocks']

    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    if len(table_blocks) <= 0:
        return "<b> NO Table FOUND </b>"

    csv = ''
    for index, table in enumerate(table_blocks):
        csv += generate_table_csv(table, blocks_map, index + 1)

    return csv


def generate_table_csv(table_result, blocks_map, table_index):
    rows, scores = get_rows_columns_map(table_result, blocks_map)

    csv = ""

    for row_index, cols in rows.items():
        for col_index, text in cols.items():
            csv += '{}'.format(text) + ","
        csv += '\n'
    return csv


def load_json(filename):
    with open(filename) as f:
        return json.load(f)

def load_csv(filename):
    with open(filename) as f:
        reader = list(csv.reader(f))

        times = {}

        dates = reader[0]
        del reader[0]
        del dates[0]
        del dates[-1]

        for date in dates:
            times[date] = {}

        for row in reader:
            name = row[0].strip()

            if not name:
                continue

            del row[0]
            del row[-1]

            for i, t in enumerate(row):
                t = t.strip()
                if t:
                    times[dates[i]][name] = t

        return times


def send_notification(data, key):
    days = {d: v for d, v in data.items() if "Guus" in v}
    n = len(days)

    body = []

    for d, v in days.items():
        dt = d.split(" ")[1].split("-")
        dt = datetime.strptime(f"{dt[0]:02}-{dt[1]}", "%d-%b") - timedelta(days=1)

        body.append(f"{dt.strftime('%A')} {v['Guus']}")

    requests.post("https://api.mynotifier.app", {
        "apiKey": key,
        "message": "New work schedule",
        "description": f"You work {n} {'time' if n == 1 else 'times'} next week",
        "body": "\n".join(body),
        "type": "info"
    })


def analyze(file_name):
    config = load_json("config.json")

    table_csv = get_table_csv_results(file_name)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not os.path.exists(f"data/{now}"):
        os.mkdir(f"data/{now}")

    filename = f"data/{now}/roster.csv"

    with open(filename, "w") as f:
        f.write(table_csv)

    data = load_csv(filename)

    send_notification(data, config["notifier_api_key"])

    # TODO: Send data to calendar


if __name__ == "__main__":
    analyze("rooster.jpeg")
