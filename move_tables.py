import os
import json

minimal_tables = [
    "ACADEMIC_TERMS",
    "ACADEMIC_TERMS_ALL",
    "ACADEMIC_TERM_PARAMETER",
    "BUILDINGS",
    "CIP",
    "CIS_COURSE_CATALOG",
    "CIS_HASS_ATTRIBUTE",
    "COURSE_CATALOG_SUBJECT_OFFERED",
    "EMPLOYEE_DIRECTORY",
    "FAC_BUILDING",
    "FAC_BUILDING_ADDRESS",
    "FAC_FLOOR",
    "FAC_ORGANIZATION",
    "FAC_ROOMS",
    "FCLT_BUILDING",
    "FCLT_BUILDING_ADDRESS",
    "FCLT_BUILDING_HIST",
    "FCLT_ORGANIZATION",
    "FCLT_ORG_DLC_KEY",
    "FCLT_ROOMS",
    "IAP_SUBJECT_CATEGORY",
    "IAP_SUBJECT_DETAIL",
    "IAP_SUBJECT_PERSON",
    "IAP_SUBJECT_SESSION",
    "IAP_SUBJECT_SPONSOR",
    "LIBRARY_COURSE_INSTRUCTOR",
    "LIBRARY_MATERIAL_STATUS",
    "LIBRARY_RESERVE_CATALOG",
    "LIBRARY_RESERVE_MATRL_DETAIL",
    "LIBRARY_SUBJECT_OFFERED",
    "MASTER_DEPT_HIERARCHY",
    "MIT_STUDENT_DIRECTORY",
    "SIS_ADMIN_DEPARTMENT",
    "SIS_COURSE_DESCRIPTION",
    "SIS_DEPARTMENT",
    "SIS_SUBJECT_CODE",
    "SPACE_DETAIL",
    "SPACE_FLOOR",
    "SPACE_SUPERVISOR_USAGE",
    "SPACE_UNIT",
    "SPACE_USAGE",
    "STUDENT_DEPARTMENT",
    "SUBJECT_OFFERED",
    "TIME_DAY",
    "TIP_DETAIL",
    "TIP_MATERIAL",
    "TIP_MATERIAL_STATUS",
    "TIP_SUBJECT_OFFERED"
]


dw_tables = []

with open("dev_tables.json", "r") as file:
    data = json.load(file)
    for table in data:
        info = data[table]
        if info["db_id"] != "dw":
            continue

        table_name = info["table_name_original"]
        if table_name not in minimal_tables:
            continue

        dw_tables.append(table_name)

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
