import json

with open("annotated_all.json") as f:
    data = json.load(f)
    keep, redact = {}, {}
    for table in data:
        for col, val in data[table].items():
            if val == "KEEP":
                if table not in keep:
                    keep[table] = []
                keep[table].append(col)
            else:
                if table not in redact:
                    redact[table] = []
                redact[table].append(col)
    with open("annotated_split.json", "w") as f:
        json.dump({"KEEP": keep, "REDACT": redact}, f, indent=2)
