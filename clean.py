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

with open("annotated_all.json") as f:
    data = json.load(f)
    keep, redact, redact_more = {}, {}, {}
    for table in data:
        for col, val in data[table].items():
            if val == "KEEP":
                if table not in keep:
                    keep[table] = []
                keep[table].append(col)
            else:
                if table in minimal_tables:
                    if table not in redact:
                        redact[table] = []
                    redact[table].append(col)
                else:
                    if table not in redact_more:
                        redact_more[table] = []
                    redact_more[table].append(col)
    with open("annotated_split.json", "w") as f:
        json.dump({"KEEP": keep, "REDACT": redact,
                  "REDACT_MORE": redact_more}, f, indent=2)
