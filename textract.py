import csv
import json
import boto3
import cv2
from datetime import datetime, timedelta
from io import StringIO

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mrt": 3,
    "apr": 4,
    "mei": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "dec": 12,
}

POSITIONS = {
    "vlees": "Meat",
    "vices": "Meat",
    "viees": "Meat",
    "afw": "Dishes"
}

FULL_TIME_HOURS = {
    "V": {
        "hour": 11,
        "minutes": 0
    },
    "Y": {
        "hour": 11,
        "minutes": 0
    },
    "L": {
        "hour": 14,
        "minutes": 30
    },
    "I": {
        "hour": 14,
        "minutes": 30
    },
    "!": {
            "hour": 14,
            "minutes": 30
        }
}


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
                        rows[row_index] = {}

                    scores.append(str(cell['Confidence']))

                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows, scores


def get_text(result, blocks_map) -> str:
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


def get_table_csv_results(file_name: str) -> str:
    img = cv2.imread(file_name, 0)

    _, im_bw = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imwrite("temp.png", im_bw)

    with open("temp.png", 'rb') as file:
        img_test = file.read()
        bytes_test = bytearray(img_test)
        print('Image loaded', file_name)

    os.remove("temp.png")

    session = boto3.Session(profile_name='default')
    client = session.client('textract', region_name='eu-west-2')
    response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['TABLES'])

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


def load_csv(data) -> list:
    reader = list(csv.reader(data))

    week = int(reader[0][0].split()[1])

    times = []

    raw_dates = reader[0]
    del reader[0]
    del raw_dates[0]
    del raw_dates[-1]

    for i, row in enumerate(reader):
        name = row[0].strip()

        if "week" in row[0].lower():
            continue

        if not name:
            continue

        del row[0]
        del row[-1]

        if ("V " in row[1:] or "L " in row[1:] or "y " in row[1:]) and len(row) > 9:
            sc = 0
            for idx, c in enumerate(row):
                if c == "":
                    sc += 1

                elif sc > 0:
                    for cidx in range(1, sc + 1):
                        row[idx - cidx] = "_"

                    for _ in range(sc // 2):
                        row.insert(idx - sc, "")

                    sc = 0

        row = [x for x in row if x != "_"]

        for j, t in enumerate(row):
            t = t.strip()

            if not t:
                continue

            date = datetime(datetime.now().year, 1, 1) + timedelta(days=(week - 1) * 7 + j)

            is_full_time = t.upper() in FULL_TIME_HOURS.keys()

            if not is_full_time:
                time_parts = [int(i) for i in t[:5].split(":")]
                start_time = {
                    "hour": time_parts[0],
                    "minutes": time_parts[1]
                }

            else:
                start_time = FULL_TIME_HOURS[t.upper()]

            end_time = None

            pos = None

            if len(t) > 5 or (is_full_time and len(t.split()) > 1):
                pos = t[5:].lower().strip() if not is_full_time else t.split()[1]

                if len(pos.split()) == 2:
                    pos = POSITIONS[pos.split()[0]]

                    time_parts = [int(i) for i in pos.split()[1].split(":")]
                    end_time = {
                        "hour": time_parts[0],
                        "minutes": time_parts[1]
                    }

                else:
                    if pos in POSITIONS:
                        pos = POSITIONS[pos]

                    elif ":" in pos:
                        time_parts = [int(i) for i in pos.split(":")]
                        end_time = {
                            "hour": time_parts[0],
                            "minutes": time_parts[1]
                        }
                        pos = None

                    else:
                        pos = None

            times.append({
                "name": name,
                "start": date.replace(hour=start_time["hour"], minute=start_time["minutes"]).strftime("%Y-%m-%d %H:%M"),
                "end": date.replace(hour=end_time["hour"], minute=end_time["minutes"]).strftime("%Y-%m-%d %H:%M") if end_time else None,
                "position": pos if pos else "None",
                "full_time": is_full_time
            })

    return times


def analyze(file_name):
    csv_data = get_table_csv_results(file_name)

    json_data = load_csv(StringIO(csv_data))

    return json_data


if __name__ == "__main__":
    print(json.dumps(analyze("test/test.jpeg")))
