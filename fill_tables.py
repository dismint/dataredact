import os
import random
random.seed(42)

EMPTY_TABLES = ['FUND_CENTER_HIERARCHY', 'PROFIT_CENTER_GROUP']
DROP_TABLES = ['FIELDS', 'TABLES']
TRUNCATE_TABLES = ['LIBRARY_RESERVE_CATALOG'] # truncate to 100k rows

redacted_tables = os.listdir("redacted")
for file in os.listdir("data"):
    if 'fields' in file.lower() or 'tables' in file.lower():
        continue
    if file not in redacted_tables:
        with open(f"data/{file}", "r") as f:
            data = f.read()
            if file.split(".")[0] in EMPTY_TABLES:
                data = data.split("\n")[0]
            if file.split(".")[0] in TRUNCATE_TABLES:
                rows = data.split("\n")
                subset = [rows[0]] + random.choices(rows[1:], k=100000)
                data = "\n".join(subset)
                print(f"truncated: {file}")
            with open(f"redacted/{file}", "w") as f2:
                f2.write(data)
        print(f"moved: {file}")
