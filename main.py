import os
import json

tbllist = []

with open("dev_tables.json", "r") as file:
    data = json.load(file)
    for table in data:
        info = data[table]
        if info["db_id"] != "dw":
            continue
        tbl = info["table_name_original"]
        tbllist.append(tbl)

# loop through all files in the original directory

good = []

for file in os.listdir("original"):
    name = file.split(".")[0]
    print(name)
    name = name.replace("_DATA_VIEW", "")
    print(name)
    if name not in tbllist:
        continue

    good.append(name)

print(len(good), good)
