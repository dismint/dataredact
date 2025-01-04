import os

redacted_tables = os.listdir("redacted")
for file in os.listdir("data"):
    if file not in redacted_tables:
        with open(f"data/{file}", "r") as f:
            data = f.read()
            with open(f"redacted/{file}", "w") as f2:
                f2.write(data)
        print(f"moved: {file}")
