import os
import json

answers = {}
counter = 0

files = os.listdir("data")
files.sort()
for file in files:
    with open(f"data/{file}", "r") as f:
        fname = file.split(".")[0].strip()
        answers[fname] = {}
        counter += 1

        rows = f.readlines()
        cols = [r.strip("\n\"") for r in rows[0].split(",")]
        for i in range(len(cols)):
            print("\n")
            print("table:", fname, counter)
            print("col:", cols[i])
            hide = input()
            if hide:
                answers[fname][cols[i]] = "REDACT"
            else:
                answers[fname][cols[i]] = "KEEP"

    with open("annotated_all.json", "w") as f:
        f.write(json.dumps(answers, indent=2))

# clean up the file

columns = 0
with open('annotated_all.json') as f:
    data = json.load(f)
    clean, redact = {}, {}
    for table in data:
        for col in data[table]:
            columns += 1
            val = data[table][col]
            if val == "REDACT":
                if table not in redact:
                    redact[table] = []
                redact[table].append(col)
            else:
                if table not in clean:
                    clean[table] = []
                clean[table].append(col)

results = {"KEEP": clean, "REDACT": redact}
with open('annotated_split.json', 'w') as f:
    f.write(json.dumps(results, indent=2))

print("total columns: ", columns)
