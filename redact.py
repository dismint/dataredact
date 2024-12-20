import os
import csv
import json
import random


#############
# LOAD DATA #
#############

# ASSETS
FNAMES, LNAMES = [], []
with open("assets/names.json") as f:
    names = json.load(f)
    FNAMES = names[0]
    LNAMES = names[1]

# POOLS
MIT_ID_POOL = set()
KERB_POOL = set()
BUILDING_AND_ROOM_POOL = set()

# DATA: original data
# VMAP: original data, except values [old, new] pairs instead
DATA, VMAP = {}, {}

for file in os.listdir("data"):
    with open(f"data/{file}") as f:
        tname = file.split(".")[0]
        info = list(csv.DictReader(f))
        if len(info) == 0:
            print(f"EMPTY: {tname}")
        DATA[tname] = info
        VMAP[tname] = [{key: [row[key], None] for key in row} for row in info]


###########
# UTILITY #
###########


def get_column(table, column):
    return [row[column] for row in DATA[table]]


def set_value_by_value(table, column, old_value, new_value):
    for row in VMAP[table]:
        if row[column][0] == old_value:
            row[column][1] = new_value


def set_value_by_index(table, column, index, new_value):
    VMAP[table][index][column][1] = new_value


def get_row_by_value(table, column, value):
    for row in VMAP[table]:
        if row[column][0] == value:
            return row
    return None


def random_mitid():
    while 1:
        id = "9" + "".join([str(random.randint(0, 9)) for _ in range(8)])
        if id not in MIT_ID_POOL:
            MIT_ID_POOL.add(id)
            return id


def random_kerb(fname, lname):
    choice = random.randint(0, 4)
    kerb = f"{fname[0]}{lname}"
    if choice <= 3:
        kerb = fname + lname[0]
    elif choice == 4:
        kerb = fname[0] + lname[0]
    kerb = kerb.lower()
    while kerb in KERB_POOL:
        kerb = kerb + str(random.randint(0, 9))
    return kerb


def random_room_for_building(building):
    while 1:
        room = str(random.randint(1, 9999))
        if random.randint(0, 1):
            room += random.choice("ABCDEFGH")
        if f"{building}-{room}" not in BUILDING_AND_ROOM_POOL:
            BUILDING_AND_ROOM_POOL.add(f"{building}-{room}")
            return room


##############
# TASK FUNCS #
##############
# note: look at the bottom of this file for the task list


def person_task(t_empl, t_student, linked):
    # EMPLOYEE DIRECTORY
    # MIT_ID
    eids = get_column(t_empl, "MIT_ID")
    for id in eids:
        if id in MIT_ID_POOL:
            print(f"DUPLICATE ID: {id}")
        MIT_ID_POOL.add(id)
    for id in eids:
        new_id = random_mitid()
        set_value_by_value(t_empl, "MIT_ID", id, new_id)

    # NAMING
    kerbs = get_column(t_empl, "KRB_NAME")
    last_names = get_column(t_empl, "LAST_NAME")
    first_names = get_column(t_empl, "FIRST_NAME")
    middle_names = get_column(t_empl, "MIDDLE_NAME")
    personal_urls = get_column(t_empl, "PERSONAL_URL")
    for kerb in kerbs:
        if not kerb:
            continue
        if kerb in KERB_POOL:
            print(f"DUPLICATE KERB: {kerb}")
        KERB_POOL.add(kerb.lower())
    for i in range(len(last_names)):
        last_name = last_names[i]
        first_name = first_names[i]
        middle_name = middle_names[i]
        if not last_name or not first_name:
            print(f"MISSING NAME: {first_name} {last_name}")
            continue
        new_lname = random.choice(LNAMES)
        new_fname = random.choice(FNAMES)
        set_value_by_index(t_empl, "LAST_NAME", i, new_lname)
        set_value_by_index(t_empl, "FIRST_NAME", i, new_fname)
        if middle_name:
            new_mname = random.choice(LNAMES)
            set_value_by_index(t_empl, "MIDDLE_NAME", i, new_mname)
            set_value_by_index(t_empl, "PREFERRED_MIDDLE_NAME", i, new_mname)
        new_full_name = f"{new_lname}, {new_fname}"
        set_value_by_index(t_empl, "FULL_NAME", i, new_full_name)
        set_value_by_index(t_empl, "FULL_NAME_UPPERCASE",
                           i, new_full_name.upper())
        set_value_by_index(t_empl, "DIRECTORY_FULL_NAME", i, new_full_name)
        kerb = random_kerb(new_fname, new_lname)
        set_value_by_index(t_empl, "KRB_NAME", i, kerb)
        set_value_by_index(t_empl, "KRB_NAME_UPPERCASE", i, kerb.upper())
        email = f"{kerb}@mit.edu"
        set_value_by_index(t_empl, "EMAIL_ADDRESS", i, email)
        set_value_by_index(t_empl, "EMAIL_ADDRESS_UPPERCASE", i, email.upper())
        if personal_urls[i]:
            set_value_by_index(t_empl, "PERSONAL_URL", i, f"{kerb}.mit.edu")
        set_value_by_index(t_empl, "NAME_KNOWN_BY", i, new_fname)
        set_value_by_index(t_empl, "PREFERRED_FIRST_NAME", i, new_fname)
        set_value_by_index(
            t_empl, "PREFERRED_FIRST_NAME_UPPER", i, new_fname.upper())
        set_value_by_index(t_empl, "PREFERRED_LAST_NAME", i, new_lname)
        set_value_by_index(
            t_empl, "PREFERRED_LAST_NAME_UPPER", i, new_lname.upper())

    # STUDENT DIRECTORY
    # NAMING
    last_names = get_column(t_student, "LAST_NAME")
    first_names = get_column(t_student, "FIRST_NAME")
    middle_names = get_column(t_student, "MIDDLE_NAME")
    for i in range(len(last_names)):
        last_name = last_names[i]
        first_name = first_names[i]
        middle_name = middle_names[i]
        if not last_name or not first_name:
            print(f"MISSING NAME: {first_name} {last_name}")
            continue
        new_lname = random.choice(LNAMES)
        new_fname = random.choice(FNAMES)
        set_value_by_index(t_student, "LAST_NAME", i, new_lname)
        set_value_by_index(t_student, "FIRST_NAME", i, new_fname)
        if middle_name:
            new_mname = random.choice(LNAMES)
            set_value_by_index(t_student, "MIDDLE_NAME", i, new_mname)
        new_full_name = f"{new_lname}, {new_fname}"
        set_value_by_index(t_student, "FULL_NAME", i, new_full_name)
        set_value_by_index(t_student, "FULL_NAME_UPPERCASE",
                           i, new_full_name.upper())
        kerb = random_kerb(new_fname, new_lname)
        set_value_by_index(t_student, "EMAIL_ADDRESS", i, f"{kerb}@mit.edu")

    # update all linked tables
    for table_name in linked:
        table = linked[table_name]
        id_col = table["ID"]

        if "NAME" in table:
            name_col = table["NAME"]
            for i, row in enumerate(VMAP[table_name]):
                id = row[id_col][0]
                name = row[name_col][0]
                if not id:
                    continue
                person = get_row_by_value(t_empl, "MIT_ID", id)
                if person:
                    set_value_by_index(table_name, name_col,
                                       i, person["FULL_NAME"][1])
                    set_value_by_index(table_name, id_col,
                                       i, person["MIT_ID"][1])
                else:
                    # print(f"MISSING: {id} {name} in {table_name}-{name_col}")
                    pass


def room_task(source):
    building_rooms = get_column(source, "BUILDING_ROOM")
    for i, br in enumerate(building_rooms):
        BUILDING_AND_ROOM_POOL.add(br)
        building = br.split("-")[0]
        new_room = random_room_for_building(building)
        building_room = f"{building}-{new_room}"
        set_value_by_index(source, "BUILDING_ROOM", i, building_room)
        set_value_by_index(source, "ROOM_NUMBER", i, new_room)
    # for rm in res:
    #     print(rm)

#########
# TASKS #
#########
# every task is set up with the information it needs


TASKS = [
    {
        "func": person_task,
        "t_empl": "EMPLOYEE_DIRECTORY",
        "t_student": "MIT_STUDENT_DIRECTORY",
        "linked": {
            "COURSE_CATALOG_SUBJECT_OFFERED": {
                "ID": "RESPONSIBLE_FACULTY_MIT_ID",
                "NAME": "RESPONSIBLE_FACULTY_NAME",
            }
        }
    },
    {
        "func": room_task,
        "source": "FCLT_ROOMS"
    }
]

for task in TASKS:
    args = []
    for key in task:
        if key != "func":
            args.append(task[key])
    task["func"](*args)
