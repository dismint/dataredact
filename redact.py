import os
import csv
import json
import random
import itertools


#############
# LOAD DATA #
#############

# ASSETS
EMAIL_SUFFIX = ["@gmail.com", "@yahoo.com", "@hotmail.com", "@aol.com"]
URL_SUFFIX = [".com", ".org", ".net", ".edu"]
FNAMES, LNAMES, USAGES = [], [], []
with open("assets/names.json") as f:
    names = json.load(f)
    FNAMES = names[0]
    LNAMES = names[1]
with open("assets/usages.json") as f:
    USAGES = json.load(f)

# POOLS
MIT_ID_POOL = set()
KERB_POOL = set()
BUILDING_AND_ROOM_POOL = set()
PHONE_POOL = set()

# QUICKFINDS
MIT_ID_MAP = {}
ROOM_MAP = {}
BUILD_ROOM_FLOOR_MAP = {}
ROOM_FLOOR_MAP = {}
RKEY_MAP = {}
BROOM_MAP = {}
BUILDING_ROOM_MAP = {}
MEET_MAP = {}
INSTRUCTOR_MAP = {}

# VMAP: original data, except values [old, new] pairs instead
VMAP = {}

for file in os.listdir("data"):
    with open(f"data/{file}") as f:
        tname = file.split(".")[0]
        header = [h.strip('"') for h in next(f).strip().split(",")]
        # limit the amount that we can read for speed purposes
        # info = list(csv.DictReader(
        #     itertools.islice(f, 2000), fieldnames=header))
        # unlimited
        info = list(csv.DictReader(f, fieldnames=header))
        if len(info) == 0:
            print(f"EMPTY: {tname}")
        VMAP[tname] = [{key: [row[key], row[key]]
                        for key in row} for row in info]
        print("finished loading:", tname)
print("\n")


###########
# UTILITY #
###########


def get_column(table, column):
    return [row[column][0] for row in VMAP[table]]


def set_value_by_index(table, column, index, new_value):
    VMAP[table][index][column][1] = new_value


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


def random_room_for_building(building, floor):
    while 1:
        room = str(floor) + \
            "".join([str(random.randint(0, 9)) for _ in range(2)])
        if random.randint(0, 1):
            room += random.choice("ABCDEFGH")
        if f"{building}-{room}" not in BUILDING_AND_ROOM_POOL:
            BUILDING_AND_ROOM_POOL.add(f"{building}-{room}")
            return room


def random_consistent_room(room):
    if room in ROOM_MAP:
        return ("-1", -1, ROOM_MAP[room])

    floor = -1
    if len(room) > 2:
        floor = room[:len(room)-2]
    else:
        floor = room
    return ("-1", floor, random_room_for_building("-1", floor))


def random_room_consider_floor(loc, room_mode=False):
    if "-" not in loc:
        return (loc, None, None)

    if room_mode:
        return random_consistent_room(loc)

    building = loc.split("-")[0].strip()
    old_room = "-".join([x.strip() for x in loc.split("-")[1:]])
    room = old_room
    found_room = False
    floor = -1
    if old_room in ROOM_MAP and ROOM_MAP[old_room] is not None:
        found_room = True
        room = ROOM_MAP[old_room]
    if loc in BUILD_ROOM_FLOOR_MAP:
        floor = BUILD_ROOM_FLOOR_MAP[loc]
        if not found_room:
            if building in ROOM_FLOOR_MAP and floor in ROOM_FLOOR_MAP[building]:
                room = random.choice(BUILD_ROOM_FLOOR_MAP[building][floor])
            else:
                room = random_room_for_building(building, floor)
    else:
        rmf = "-".join([x.strip() for x in loc.split("-")[1:]])
        _, floor, troom = random_consistent_room(rmf)
        if not found_room:
            room = troom
    if not found_room:
        if old_room not in ROOM_MAP:
            ROOM_MAP[old_room] = room
    assert room is not None, f"room is None for {loc}"
    return (building, floor, room)


##############
# TASK FUNCS #
##############
# note: look at the bottom of this file for the task list


def person_task(related):
    fields = [
        "MIT_ID",
        "LAST_NAME",
        "FIRST_NAME",
        "MIDDLE_NAME",
        "FULL_NAME",
        "FULL_NAME2",
        "FULL_NAME3",
        "FULL_NAME_UPPERCASE",
        "DIRECTORY_FULL_NAME",
        "KRB_NAME",
        "KRB_NAME_UPPERCASE",
        "EMAIL_ADDRESS",
        "EMAIL_ADDRESS_UPPERCASE",
        "PERSONAL_URL",
        "NAME_KNOWN_BY",
        "PREFERRED_FIRST_NAME_UPPER",
        "PREFERRED_LAST_NAME_UPPER",
        "PREFERRED_FIRST_NAME",
        "PREFERRED_MIDDLE_NAME",
        "PREFERRED_LAST_NAME",
        "OFFICE_PHONE",
    ]
    # add all MIT_ID first
    for table_name, table in related:
        if "MIT_ID" in table:
            ids = get_column(table_name, table["MIT_ID"])
            for id in ids:
                if id:
                    MIT_ID_POOL.add(id)
        if "KRB_NAME" in table:
            krb_names = get_column(table_name, "KRB_NAME")
            for krb in krb_names:
                if krb:
                    KERB_POOL.add(krb.lower())
        if "OFFICE_PHONE" in table:
            phones = get_column(table_name, "OFFICE_PHONE")
            for phone in phones:
                if phone:
                    PHONE_POOL.add(phone)

    for table_name, table in related:
        # this is a bit of a hacky way to make this function also work
        # even if it doesn't have an MIT_ID as one of the columns
        ids = get_column(
            table_name, table["MIT_ID"] if "MIT_ID" in table else list(table.values())[0])
        for i, id in enumerate(ids):
            fill_fields = set(field for field in table)
            if id in MIT_ID_MAP:
                mapping = MIT_ID_MAP[id]
                for field in table:
                    assert field in fields, f"{field} not in fields"
                    field_name = table[field]
                    try:
                        set_value_by_index(
                            table_name, field_name, i, mapping[field])
                        fill_fields.remove(field)
                    except:
                        pass

            def check_val(field):
                return field in table and VMAP[table_name][i][table[field]][0] != ""

            def need(field):
                return field in fill_fields

            if id and id not in MIT_ID_MAP:
                new_id = random_mitid()
                MIT_ID_MAP[id] = {}
                if "MIT_ID" in table:
                    set_value_by_index(table_name, table["MIT_ID"], i, new_id)
                MIT_ID_MAP[id]["MIT_ID"] = new_id
                MIT_ID_MAP[id]["CREATED_TABLE"] = table_name
            if not id:
                MIT_ID_MAP["NOID"] = {}
                id = "NOID"

            new_fname = random.choice(FNAMES)
            if "FIRST_NAME" in table and check_val("FIRST_NAME") and need("FIRST_NAME"):
                set_value_by_index(
                    table_name, table["FIRST_NAME"], i, new_fname)
                MIT_ID_MAP[id]["FIRST_NAME"] = new_fname

            new_lname = random.choice(LNAMES)
            if "LAST_NAME" in table and check_val("LAST_NAME") and need("LAST_NAME"):
                set_value_by_index(
                    table_name, table["LAST_NAME"], i, new_lname)
                MIT_ID_MAP[id]["LAST_NAME"] = new_lname

            new_mname = random.choice(LNAMES)
            if "MIDDLE_NAME" in table and check_val("MIDDLE_NAME") and need("MIDDLE_NAME"):
                set_value_by_index(
                    table_name, table["MIDDLE_NAME"], i, new_mname)
                MIT_ID_MAP[id]["MIDDLE_NAME"] = new_mname

            new_full_name = f"{new_lname}, {new_fname}"
            if "MIDDLE_NAME" in MIT_ID_MAP[id]:
                new_full_name = f"{new_lname}, {new_fname} {new_mname}."
            if "FULL_NAME" in table and check_val("FULL_NAME") and need("FULL_NAME"):
                set_value_by_index(
                    table_name, table["FULL_NAME"], i, new_full_name)
                MIT_ID_MAP[id]["FULL_NAME"] = new_full_name

            # hacky solution for now to allow multiple full names
            if "FULL_NAME2" in table and check_val("FULL_NAME2") and need("FULL_NAME2"):
                if "INSTRUCTOR" in table["FULL_NAME2"]:
                    new_full_name = f"{new_fname[0]}. {new_mname[0]}. {new_lname}"
                original = VMAP[table_name][i][table["FULL_NAME2"]][0]
                if original in INSTRUCTOR_MAP:
                    new_full_name = INSTRUCTOR_MAP[original]
                set_value_by_index(
                    table_name, table["FULL_NAME2"], i, new_full_name)
                INSTRUCTOR_MAP[original] = new_full_name
                MIT_ID_MAP[id]["FULL_NAME2"] = new_full_name
            if "FULL_NAME3" in table and check_val("FULL_NAME3") and need("FULL_NAME3"):
                if "INSTRUCTOR" in table["FULL_NAME3"]:
                    new_full_name = f"{new_fname[0]}. {new_mname[0]}. {new_lname}"
                original = VMAP[table_name][i][table["FULL_NAME3"]][0]
                if original in INSTRUCTOR_MAP:
                    new_full_name = INSTRUCTOR_MAP[original]
                set_value_by_index(
                    table_name, table["FULL_NAME3"], i, new_full_name)
                INSTRUCTOR_MAP[original] = new_full_name
                MIT_ID_MAP[id]["FULL_NAME3"] = new_full_name

            new_full_name_upper = new_full_name.upper()
            if "FULL_NAME_UPPERCASE" in table and check_val("FULL_NAME_UPPERCASE") and need("FULL_NAME_UPPERCASE"):
                set_value_by_index(
                    table_name, table["FULL_NAME_UPPERCASE"], i, new_full_name_upper)
                MIT_ID_MAP[id]["FULL_NAME_UPPERCASE"] = new_full_name_upper

            new_directory_full_name = new_full_name
            if "DIRECTORY_FULL_NAME" in table and check_val("DIRECTORY_FULL_NAME") and need("DIRECTORY_FULL_NAME"):
                set_value_by_index(
                    table_name, table["DIRECTORY_FULL_NAME"], i, new_directory_full_name)
                MIT_ID_MAP[id]["DIRECTORY_FULL_NAME"] = new_directory_full_name

            kerb = random_kerb(new_fname, new_lname)
            if "KRB_NAME" in table and check_val("KRB_NAME") and need("KRB_NAME"):
                set_value_by_index(table_name, table["KRB_NAME"], i, kerb)
                MIT_ID_MAP[id]["KRB_NAME"] = kerb

            kerb_upper = kerb.upper()
            if "KRB_NAME_UPPERCASE" in table and check_val("KRB_NAME_UPPERCASE") and need("KRB_NAME_UPPERCASE"):
                set_value_by_index(
                    table_name, table["KRB_NAME_UPPERCASE"], i, kerb_upper)
                MIT_ID_MAP[id]["KRB_NAME_UPPERCASE"] = kerb.upper()

            email = f"{kerb}{random.choice(EMAIL_SUFFIX)}"
            if "EMAIL_ADDRESS" in table and check_val("EMAIL_ADDRESS") and need("EMAIL_ADDRESS"):
                set_value_by_index(
                    table_name, table["EMAIL_ADDRESS"], i, email)
                MIT_ID_MAP[id]["EMAIL_ADDRESS"] = email

            email_upper = email.upper()
            if "EMAIL_ADDRESS_UPPERCASE" in table and check_val("EMAIL_ADDRESS_UPPERCASE") and need("EMAIL_ADDRESS_UPPERCASE"):
                set_value_by_index(
                    table_name, table["EMAIL_ADDRESS_UPPERCASE"], i, email_upper)
                MIT_ID_MAP[id]["EMAIL_ADDRESS_UPPERCASE"] = email_upper

            personal_url = f"{kerb}{random.choice(URL_SUFFIX)}"
            if "PERSONAL_URL" in table and check_val("PERSONAL_URL") and need("PERSONAL_URL"):
                set_value_by_index(
                    table_name, table["PERSONAL_URL"], i, personal_url)
                MIT_ID_MAP[id]["PERSONAL_URL"] = personal_url

            if "NAME_KNOWN_BY" in table and check_val("NAME_KNOWN_BY") and need("NAME_KNOWN_BY"):
                set_value_by_index(
                    table_name, table["NAME_KNOWN_BY"], i, new_fname)
                MIT_ID_MAP[id]["NAME_KNOWN_BY"] = new_fname

            if "PREFERRED_FIRST_NAME" in table and check_val("PREFERRED_FIRST_NAME") and need("PREFERRED_FIRST_NAME"):
                set_value_by_index(
                    table_name, table["PREFERRED_FIRST_NAME"], i, new_fname)
                MIT_ID_MAP[id]["PREFERRED_FIRST_NAME"] = new_fname

            if "PREFERRED_FIRST_NAME_UPPER" in table and check_val("PREFERRED_FIRST_NAME_UPPER") and need("PREFERRED_FIRST_NAME_UPPER"):
                set_value_by_index(
                    table_name, table["PREFERRED_FIRST_NAME_UPPER"], i, new_fname.upper())
                MIT_ID_MAP[id]["PREFERRED_FIRST_NAME_UPPER"] = new_fname.upper()

            if "PREFERRED_LAST_NAME" in table and check_val("PREFERRED_LAST_NAME") and need("PREFERRED_LAST_NAME"):
                set_value_by_index(
                    table_name, table["PREFERRED_LAST_NAME"], i, new_lname)
                MIT_ID_MAP[id]["PREFERRED_LAST_NAME"] = new_lname

            if "PREFERRED_LAST_NAME_UPPER" in table and check_val("PREFERRED_LAST_NAME_UPPER") and need("PREFERRED_LAST_NAME_UPPER"):
                set_value_by_index(
                    table_name, table["PREFERRED_LAST_NAME_UPPER"], i, new_lname.upper())
                MIT_ID_MAP[id]["PREFERRED_LAST_NAME_UPPER"] = new_lname.upper()

            if "PREFERRED_MIDDLE_NAME" in table and check_val("PREFERRED_MIDDLE_NAME") and need("PREFERRED_MIDDLE_NAME"):
                set_value_by_index(
                    table_name, table["PREFERRED_MIDDLE_NAME"], i, new_mname)
                MIT_ID_MAP[id]["PREFERRED_MIDDLE_NAME"] = new_mname

            if "OFFICE_PHONE" in table and check_val("OFFICE_PHONE") and need("OFFICE_PHONE"):
                new_phone = "".join([str(random.randint(0, 9))
                                    for _ in range(10)])
                set_value_by_index(
                    table_name, table["OFFICE_PHONE"], i, new_phone)
                MIT_ID_MAP[id]["OFFICE_PHONE"] = new_phone


def room_task(source, related):
    building_rooms = get_column(source, "BUILDING_ROOM")
    rooms = get_column(source, "ROOM")
    rkey = get_column(source, "FCLT_ROOM_KEY")
    floors = get_column(source, "FLOOR")
    for i, br in enumerate(building_rooms):
        BUILDING_AND_ROOM_POOL.add(br)
        building = br.split("-")[0]
        new_room = random_room_for_building(building, floors[i])
        new_building_room = f"{building}-{new_room}"
        set_value_by_index(source, "FCLT_ROOM_KEY", i, new_building_room)
        set_value_by_index(source, "BUILDING_ROOM", i, new_building_room)
        set_value_by_index(source, "ROOM", i, new_room)
        set_value_by_index(source, "SPACE_ID", i,
                           f"{building}-{floors[i]}-{new_room}")
        if building not in BUILDING_ROOM_MAP:
            BUILDING_ROOM_MAP[building] = []
        if building not in ROOM_FLOOR_MAP:
            ROOM_FLOOR_MAP[building] = {}
        if floors[i] not in ROOM_FLOOR_MAP[building]:
            ROOM_FLOOR_MAP[building][floors[i]] = []
        ROOM_FLOOR_MAP[building][floors[i]].append(new_room)
        if br not in BUILD_ROOM_FLOOR_MAP:
            BUILD_ROOM_FLOOR_MAP[building] = {}
        BUILD_ROOM_FLOOR_MAP[br] = floors[i]
        BUILDING_ROOM_MAP[building].append(new_room)
        if rooms[i] not in ROOM_MAP:
            ROOM_MAP[rooms[i]] = new_room
        RKEY_MAP[rkey[i]] = new_building_room
        BROOM_MAP[building_rooms[i]] = new_building_room

    for table_name, table in related:
        for field in table:
            cols = get_column(table_name, table[field])
            if field == "ROOM":
                for i, room in enumerate(cols):
                    if room in ROOM_MAP:
                        set_value_by_index(
                            table_name, table[field], i, ROOM_MAP[room])
                    else:
                        _, _, new_room = random_room_consider_floor(
                            room, room_mode=True)
                        set_value_by_index(
                            table_name, table[field], i, new_room)
                        ROOM_MAP[room] = new_room
            if field == "ROOM_NO_FLOOR":
                floors = [str(x) for x in get_column(table_name, "FLOOR_KEY")]
                for i, only_room in enumerate(cols):
                    room = f"{floors[i]}{only_room}"
                    if room in ROOM_MAP:
                        set_value_by_index(
                            table_name, table[field], i, ROOM_MAP[room][len(floors[i]):])
                    else:
                        _, _, new_room = random_room_consider_floor(
                            room, room_mode=True)
                        assert new_room is not None, f"new_room is None for {room}"
                        set_value_by_index(
                            table_name, table[field], i, new_room[len(floors[i]):])
                        ROOM_MAP[room] = new_room
            if "BUILDING_ROOM" in field:
                for i, room in enumerate(cols):
                    new_building_room = -1
                    building, _, new_room = random_room_consider_floor(room)
                    if not room:
                        new_building_room = f"{building}"
                    else:
                        new_building_room = f"{building}-{new_room}"
                    set_value_by_index(
                        table_name, table[field], i, new_building_room)
            if field == "ALL_ROOM":
                for i, all_room in enumerate(cols):
                    info = all_room.split("-")
                    room = f"{info[0]}-{'-'.join(info[2:])}"
                    floor = info[1]
                    new_building_room = -1
                    building, _, new_room = random_room_consider_floor(room)
                    if not room:
                        new_building_room = f"{building}"
                    else:
                        new_building_room = f"{building}-{floor}-{new_room}"
                    set_value_by_index(
                        table_name, table[field], i, new_building_room)
            if field == "FCLT_ROOM_KEY":
                for i, room in enumerate(cols):
                    if room in RKEY_MAP:
                        set_value_by_index(
                            table_name, table[field], i, RKEY_MAP[room])
                    else:
                        print(f"ROOM {room} NOT FOUND IN RKEY_MAP")


def admin_task(source):
    for i, row in enumerate(VMAP[source]):
        new_phone = "".join([str(random.randint(0, 9)) for _ in range(10)])
        area, number = row["DEPARTMENT_PHONE_AREA_CODE"][0], row["DEPARTMENT_PHONE_NUMBER"][0]
        if area:
            set_value_by_index(
                source, "DEPARTMENT_PHONE_NUMBER", i, new_phone[:3])
        if number:
            set_value_by_index(
                source, "DEPARTMENT_PHONE_NUMBER", i, new_phone[3:])


def meet_task(related):
    cols = []
    for table_name in related:
        cols.extend(get_column(table_name, "MEET_PLACE"))
    for loc in cols:
        if loc not in MEET_MAP:
            building, _, room = random_room_consider_floor(loc)
            if not room:
                MEET_MAP[loc] = f"{building}"
            else:
                MEET_MAP[loc] = f"{building}-{room}"
    for table_name in related:
        for i, loc in enumerate(get_column(table_name, "MEET_PLACE")):
            if not loc:
                continue
            set_value_by_index(table_name, "MEET_PLACE", i, MEET_MAP[loc])


def session_task(source):
    for i, row in enumerate(VMAP[source]):
        location = row["SESSION_LOCATION"][0].lower()
        if "virtual" in location:
            set_value_by_index(source, "SESSION_LOCATION", i, "Virtual")
        elif "zoom" in location:
            loc = "Zoom"
            if any(char.isdigit() for char in location):
                loc += " "
                for char in location:
                    if char.isdigit():
                        loc += str(random.randint(0, 9))
            set_value_by_index(source, "SESSION_LOCATION", i, loc)
        else:
            set_value_by_index(source, "SESSION_LOCATION", i, "In-Person")


def subject_task(source):
    for i, row in enumerate(VMAP[source]):
        fname, lname = random.choice(FNAMES), random.choice(LNAMES)
        kerb = random_kerb(fname, lname)
        email = f"{kerb}{random.choice(EMAIL_SUFFIX)}"
        if row["PERSON_NAME"][0]:
            set_value_by_index(source, "PERSON_NAME", i, f"{fname} {lname}")
        if row["PERSON_EMAIL"][0]:
            set_value_by_index(source, "PERSON_EMAIL", i, email)
        if row["PERSON_LOCATION"][0]:
            loc = row["PERSON_LOCATION"][0]
            if loc in MEET_MAP:
                set_value_by_index(source, "PERSON_LOCATION", i, MEET_MAP[loc])
            else:
                new_loc = random.choice(list(BROOM_MAP))
                building = loc.split("-")[0]
                if building in BUILDING_ROOM_MAP:
                    new_loc = f"{building}-{random.choice(list(BUILDING_ROOM_MAP[building]))}"
                set_value_by_index(source, "PERSON_LOCATION", i, new_loc)

            # weird case
            if "[" in VMAP[source][i]["PERSON_LOCATION"][1]:
                print("ERROR:", VMAP[source][i]["PERSON_LOCATION"][1])


def library_task(related, name):
    lname_map = {}
    for i in range(len(VMAP[name])):
        fname, lname = random.choice(FNAMES), random.choice(LNAMES)
        set_value_by_index(name, "INSTRUCTOR_NAME", i, f"{lname}, {fname}")
        key = VMAP[name][i]["LIBRARY_COURSE_INSTRUCTOR_KEY"][0]
        if key not in lname_map:
            lname_map[key] = lname.upper()
    cols = []
    key_mapping = {}
    for table_name in related:
        cols.extend(get_column(table_name, "LIBRARY_COURSE_INSTRUCTOR_KEY"))
    for i, key in enumerate(cols):
        info = key.split("-")
        front, back = info[0], "".join(info[1:])
        new_back = back.lstrip(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
        if key in lname_map:
            new_key = front + "-" + lname_map[key] + new_back
        else:
            new_key = front + "-" + random.choice(LNAMES).upper() + new_back
        key_mapping[key] = new_key
    for table_name in related:
        for i, key in enumerate(get_column(table_name, "LIBRARY_COURSE_INSTRUCTOR_KEY")):
            if key in key_mapping:
                set_value_by_index(
                    table_name, "LIBRARY_COURSE_INSTRUCTOR_KEY", i, key_mapping[key])


def usage_task(source):
    for i, row in enumerate(VMAP[source]):
        if row["SPACE_USAGE"][0]:
            set_value_by_index(source, "SPACE_USAGE", i, random.choice(USAGES))


def clamp_task(area, integers):
    for table_name, column in area.items():
        cols = get_column(table_name, column)
        for i, num in enumerate(cols):
            if num:
                val = random.uniform(float(num) * 0.95, float(num) * 1.05)
                if type(num) == str:
                    val = str(val)
                set_value_by_index(table_name, column, i, val)
    for table_name, column in integers.items():
        cols = get_column(table_name, column)
        nums = [int(num) for num in cols if num]
        min_num, max_num = min(nums), max(nums)
        for i, num in enumerate(cols):
            if num:
                val = random.randint(min_num, max_num)
                val = round(val, -1)  # round to the nearest 10
                if type(num) == str:
                    val = str(val)
                set_value_by_index(table_name, column, i, val)


#########
# TASKS #
#########
# every task is set up with the information it needs
TASKS = [
    {
        "func": person_task,
        "related": [
            ["EMPLOYEE_DIRECTORY", {
                "MIT_ID": "MIT_ID",
                "FULL_NAME": "FULL_NAME",
                "FULL_NAME_UPPERCASE": "FULL_NAME_UPPERCASE",
                "DIRECTORY_FULL_NAME": "DIRECTORY_FULL_NAME",
                "LAST_NAME": "LAST_NAME",
                "FIRST_NAME": "FIRST_NAME",
                "MIDDLE_NAME": "MIDDLE_NAME",
                "KRB_NAME": "KRB_NAME",
                "KRB_NAME_UPPERCASE": "KRB_NAME_UPPERCASE",
                "EMAIL_ADDRESS": "EMAIL_ADDRESS",
                "EMAIL_ADDRESS_UPPERCASE": "EMAIL_ADDRESS_UPPERCASE",
                "PERSONAL_URL": "PERSONAL_URL",
                "NAME_KNOWN_BY": "NAME_KNOWN_BY",
                "PREFERRED_FIRST_NAME": "PREFERRED_FIRST_NAME",
                "PREFERRED_FIRST_NAME_UPPER": "PREFERRED_FIRST_NAME_UPPER",
                "PREFERRED_LAST_NAME": "PREFERRED_LAST_NAME",
                "PREFERRED_LAST_NAME_UPPER": "PREFERRED_LAST_NAME_UPPER",
                "PREFERRED_MIDDLE_NAME": "PREFERRED_MIDDLE_NAME",
                "OFFICE_PHONE": "OFFICE_PHONE",
            }],
            ["MIT_STUDENT_DIRECTORY", {
                "FIRST_NAME": "FIRST_NAME",
                "LAST_NAME": "LAST_NAME",
                "MIDDLE_NAME": "MIDDLE_NAME",
                "FULL_NAME": "FULL_NAME",
                "EMAIL_ADDRESS": "EMAIL_ADDRESS",
                "FULL_NAME_UPPERCASE": "FULL_NAME_UPPERCASE",
                "OFFICE_PHONE": "OFFICE_PHONE",
            }],
            ["LIBRARY_SUBJECT_OFFERED", {
                "MIT_ID": "RESPONSIBLE_FACULTY_MIT_ID",
                "FULL_NAME": "RESPONSIBLE_FACULTY_NAME",
            }],
            ["COURSE_CATALOG_SUBJECT_OFFERED", {
                "MIT_ID": "RESPONSIBLE_FACULTY_MIT_ID",
                "FULL_NAME": "RESPONSIBLE_FACULTY_NAME",
                "FULL_NAME2": "FALL_INSTRUCTORS",
                "FULL_NAME3": "SPRING_INSTRUCTORS",
            }],
            ["TIP_SUBJECT_OFFERED", {
                "MIT_ID": "RESPONSIBLE_FACULTY_MIT_ID",
                "FULL_NAME": "RESPONSIBLE_FACULTY_NAME",
            }],
            ["SUBJECT_OFFERED", {
                "MIT_ID": "RESPONSIBLE_FACULTY_MIT_ID",
                "FULL_NAME": "RESPONSIBLE_FACULTY_NAME",
            }],
            ["SPACE_SUPERVISOR_USAGE", {
                "MIT_ID": "MIT_ID",
            }],
            ["CIS_COURSE_CATALOG", {
                "FULL_NAME2": "FALL_INSTRUCTORS",
                "FULL_NAME3": "SPRING_INSTRUCTORS",
            }],
        ]
    },
    {
        "func": room_task,
        "source": "FCLT_ROOMS",
        "related": [
            ["FAC_ROOMS", {
                "ROOM": "ROOM",
                "FCLT_ROOM_KEY": "FAC_ROOM_KEY",
                "ALL_ROOM": "SPACE_ID",
            }],
            ["EMPLOYEE_DIRECTORY", {
                "BUILDING_ROOM": "OFFICE_LOCATION"
            }],
            ["MIT_STUDENT_DIRECTORY", {
                "BUILDING_ROOM": "OFFICE_LOCATION"
            }],
            ["SPACE_DETAIL", {
                "BUILDING_ROOM": "BUILDING_ROOM_NAME",
                "BUILDING_ROOM2": "BUILDING_ROOM",
                "ROOM_NO_FLOOR": "ROOM_NUMBER"
            }],
        ]
    },
    {
        "func": admin_task,
        "source": "SIS_ADMIN_DEPARTMENT"
    },
    {
        "func": meet_task,
        "related": [
            "COURSE_CATALOG_SUBJECT_OFFERED",
            "SUBJECT_OFFERED",
        ]
    },
    {
        "func": session_task,
        "source": "IAP_SUBJECT_SESSION",
    },
    {
        "func": subject_task,
        "source": "IAP_SUBJECT_PERSON",
    },
    {
        "func": library_task,
        "related": ["LIBRARY_COURSE_INSTRUCTOR", "LIBRARY_RESERVE_MATRL_DETAIL"],
        "name": "LIBRARY_COURSE_INSTRUCTOR",
    },
    {
        "func": usage_task,
        "source": "SPACE_USAGE",
    },
    {
        "func": clamp_task,
        "area": {
            "BUILDINGS": "BLDG_GROSS_SQUARE_FOOTAGE",
            "BUILDINGS": "BLDG_ASSIGNABLE_SQUARE_FOOTAGE",
            "FAC_BUILDING": "EXT_GROSS_AREA",
            "FAC_BUILDING": "ASSIGNABLE_AREA",
            "FAC_BUILDING": "NON_ASSIGNABLE_AREA",
            "FAC_BUILDING": "BUILDING_HEIGHT",
            "FAC_FLOOR": "EXT_GROSS_AREA",
            "FAC_FLOOR": "ASSIGNABLE_AREA",
            "FAC_FLOOR": "NON_ASSIGNABLE_AREA",
            "FAC_ROOMS": "AREA",
            "FCLT_BUILDING": "ASSIGNABLE_AREA",
            "FCLT_BUILDING": "NON_ASSIGNABLE_AREA",
            "FCLT_BUILDING": "BUILDING_HEIGHT",
            "FCLT_BUILDING": "EXT_GROSS_AREA",
            "FCLT_BUILDING": "ASSIGNABLE_AREA",
            "FCLT_BUILDING": "NON_ASSIGNABLE_AREA",
            "FCLT_BUILDING": "BUILDING_HEIGHT",
            "FCLT_ROOMS": "AREA",
            "SPACE_DETAIL": "ROOM_SQUARE_FOOTAGE",
            "SPACE_SUPERVISOR_USAGE": "SQFT",
            "SPACE_SUPERVISOR_USAGE": "RESEARCH_VOLUME",
            "SPACE_SUPERVISOR_USAGE": "SQFT_PER_SUPERVISEE",
            "SPACE_SUPERVISOR_USAGE": "SQFT_PER_RES_VOL",
            "SPACE_SUPERVISOR_USAGE": "RES_VOL_PER_SQFT",
        },
        "integers": {
            "FCLT_BUILDING": "NUM_OF_ROOMS",
            "FAC_BUILDING": "NUM_OF_ROOMS",
            "FCLT_BUILDING_HIST": "NUM_OF_ROOMS",
            "IAP_SUBJECT_DETAIL": "MAX_ENROLLMENT",
            "LIBRARY_SUBJECT_OFFERED": "NUM_ENROLLED_STUDENTS",
            "SUBJECT_OFFERED": "NUM_ENROLLED_STUDENTS"
        }
    }
]

for task in TASKS:
    print("starting:", task["func"].__name__)
    args = []
    for key in task:
        if key != "func":
            args.append(task[key])
    task["func"](*args)

print("\n")

if not os.path.exists("redacted"):
    os.makedirs("redacted")
for table_name in VMAP:
    with open(f"redacted/{table_name}.csv", "w") as f:
        writer = csv.writer(f)
        header = [key for key in VMAP[table_name][0]]
        writer.writerow(header)
        for row in VMAP[table_name]:
            writer.writerow([row[key][1] for key in row])
    print("finished writing:", table_name)
