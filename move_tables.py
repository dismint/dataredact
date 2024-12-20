import os
import json

dw_tables = []

with open("dev_tables.json", "r") as file:
    data = json.load(file)
    for table in data:
        info = data[table]
        if info["db_id"] != "dw":
            continue
        dw_tables.append(info["table_name_original"])

if not os.path.exists("data"):
    os.makedirs("data")

table_counter = 0
for file in os.listdir("original"):
    name = file.split(".")[0].replace("_DATA_VIEW", "")
    if name not in dw_tables:
        continue
    table_counter += 1
    with open(f"original/{file}", "r") as f:
        data = f.read()
        with open(f"data/{name}.csv", "w") as f2:
            f2.write(data)


print(f"moved {table_counter} tables to data folder")
