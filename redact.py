import os
import csv
import json
import random
import pandas
import itertools

# seed random for reproducibility
random.seed(0)

#############
# LOAD DATA #
#############

# ASSETS
EMAIL_SUFFIX = ["@gmail.com", "@yahoo.com", "@hotmail.com", "@aol.com", "@mail.com", "@worker.com",
                "@learner.net", "@referer.com", "@employee.com", "@gmail.business.com", "@yahoo.ca.com"]
URL_SUFFIX = [".com", ".org", ".net", ".edu"]
FNAMES, LNAMES, USAGES, TITLES = [], [], [], []
with open("assets/names.json") as f:
    names = json.load(f)
    FNAMES = names[0]
    LNAMES = names[1]
with open("assets/usages.json") as f:
    USAGES = json.load(f)
with open("assets/titles.json") as f:
    TITLES = json.load(f)

# POOLS
MIT_ID_POOL = set()
KERB_POOL = set()
BUILDING_AND_ROOM_POOL = set()
PHONE_POOL = set()

# QUICKFINDS and MAPS
BUILD_ROOM_FLOOR_MAP = {}
BUILDING_ROOM_MAP = {}
EMAIL_DOMAIN_MAP = {}
ROOM_FLOOR_MAP = {}
INSTRUCTOR_MAP = {}
MIT_ID_MAP = {}
TITLE_MAP = {}
USAGE_MAP = {}
BROOM_MAP = {}
PHONE_MAP = {}
ZOOM_MAP = {}
KERB_MAP = {}
ROOM_MAP = {}
RKEY_MAP = {}
MEET_MAP = {}

# VMAP: original data, except values [old, new] pairs instead
VMAP = {}

old_tables, more_tables = [], []
with open("annotated_split.json") as f:
    data = json.load(f)
    old_tables = [t for t in data["REDACT"]]
    more_tables = [t for t in data["REDACT_MORE"]]

for tname in old_tables:
    # unlimited
    info = pandas.read_csv(f"data/{tname}.csv", engine="pyarrow")
    # limit the amount that we can read for speed purposes
    # info = pandas.read_csv(f"data/{tname}.csv", nrows=1000)
    # info = list(csv.DictReader(f, fieldnames=header))
    if len(info) == 0:
        print(f"EMPTY: {tname}")

    headers = [h.strip('"') for h in info.columns]
    VMAP[tname] = {header: [[x, x] for x in info[header].tolist()]
                   for header in headers}
    print("finished loading:", tname)
print("\n")


###########
# UTILITY #
###########


def get_column(table, column):
    return [x[0] for x in VMAP[table][column]]


def set_value_by_index(table, column, index, new_value):
    VMAP[table][column][index][1] = new_value


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


def hide_zoom_id(data, keyword):
    start = data.lower().find(keyword)
    if start == -1:
        return data
    beginning, end = -1, -1
    for j, char in enumerate(data[start + len(keyword):]):
        if j > 20:
            break
        if char.isdigit():
            if beginning == -1:
                beginning = j
            end = j
    if beginning == -1 or end == -1:
        return data
    zoom_id = data[start + len(keyword) +
                   beginning:start + len(keyword) + end + 1]
    new_zoom_id = ""
    for char in zoom_id:
        if char.isdigit():
            new_zoom_id += random.choice("0123456789")
        else:
            new_zoom_id += char
    if zoom_id in ZOOM_MAP:
        new_zoom_id = ZOOM_MAP[zoom_id]
    ZOOM_MAP[zoom_id] = new_zoom_id
    new_data = data[:start + len(keyword) + beginning] + \
        new_zoom_id + data[start + len(keyword) + end + 1:]
    return new_data

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
        "FULL_NAME_FL",
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
            fill_fields = set()
            for field in table:
                val = VMAP[table_name][table[field]][i][0]
                if val and val == val:
                    fill_fields.add(field)
            if id in MIT_ID_MAP:
                mapping = MIT_ID_MAP[id]
                fill_fields_copy = fill_fields.copy()
                for field in fill_fields_copy:
                    field_name = table[field]
                    try:
                        set_value_by_index(
                            table_name, field_name, i, mapping[field])
                        fill_fields.remove(field)
                    except:
                        pass

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
            if "FIRST_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["FIRST_NAME"], i, new_fname)
                MIT_ID_MAP[id]["FIRST_NAME"] = new_fname

            new_lname = random.choice(LNAMES)
            if "LAST_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["LAST_NAME"], i, new_lname)
                MIT_ID_MAP[id]["LAST_NAME"] = new_lname

            new_mname = random.choice(LNAMES)
            if random.randint(0, 1):
                new_mname = new_mname[0]
            if "MIDDLE_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["MIDDLE_NAME"], i, new_mname)
                MIT_ID_MAP[id]["MIDDLE_NAME"] = new_mname

            new_full_name = f"{new_lname}, {new_fname}"
            if "MIDDLE_NAME" in MIT_ID_MAP[id]:
                new_full_name = f"{new_lname}, {new_fname} {new_mname}."
            if "FULL_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["FULL_NAME"], i, new_full_name)
                MIT_ID_MAP[id]["FULL_NAME"] = new_full_name

            new_full_name_fl = f"{new_lname}, {new_fname}"
            if "FULL_NAME_FL" in fill_fields:
                set_value_by_index(
                    table_name, table["FULL_NAME_FL"], i, new_full_name_fl)
                MIT_ID_MAP[id]["FULL_NAME_FL"] = new_full_name_fl

            new_full_name_upper = new_full_name.upper()
            if "FULL_NAME_UPPERCASE" in fill_fields:
                set_value_by_index(
                    table_name, table["FULL_NAME_UPPERCASE"], i, new_full_name_upper)
                MIT_ID_MAP[id]["FULL_NAME_UPPERCASE"] = new_full_name_upper

            # hacky solution for now to allow multiple full names
            if "FULL_NAME2" in fill_fields:
                new_i_names = []
                for i_name_raw in VMAP[table_name][table["FULL_NAME2"]][i][0].split(","):
                    i_name = i_name_raw.strip()
                    temp_fname = random.choice(FNAMES)
                    temp_lname = random.choice(LNAMES)
                    temp_mname = random.choice(LNAMES)
                    new_full_name = f"{temp_fname[0]}. {temp_mname[0]}. {temp_lname}"
                    if random.randint(0, 1):
                        new_full_name = f"{temp_fname[0]}. {temp_lname}"
                    if "staff" in i_name.lower():
                        new_full_name = "Staff"
                    if i_name in INSTRUCTOR_MAP:
                        new_full_name = INSTRUCTOR_MAP[i_name]
                    INSTRUCTOR_MAP[i_name] = new_full_name
                    new_i_names.append(new_full_name)

                new_full_name2 = ", ".join(new_i_names)
                set_value_by_index(
                    table_name, table["FULL_NAME2"], i, new_full_name2)
                MIT_ID_MAP[id]["FULL_NAME2"] = new_full_name2
            if "FULL_NAME3" in fill_fields:
                new_i_names = []
                for i_name_raw in VMAP[table_name][table["FULL_NAME3"]][i][0].split(","):
                    i_name = i_name_raw.strip()
                    temp_fname = random.choice(FNAMES)
                    temp_lname = random.choice(LNAMES)
                    temp_mname = random.choice(LNAMES)
                    new_full_name = f"{temp_fname[0]}. {temp_mname[0]}. {temp_lname}"
                    if random.randint(0, 1):
                        new_full_name = f"{temp_fname[0]}. {temp_lname}"
                    if "staff" in i_name.lower():
                        new_full_name = "Staff"
                    if i_name in INSTRUCTOR_MAP:
                        new_full_name = INSTRUCTOR_MAP[i_name]
                    INSTRUCTOR_MAP[i_name] = new_full_name
                    new_i_names.append(new_full_name)

                new_full_name2 = ", ".join(new_i_names)
                set_value_by_index(
                    table_name, table["FULL_NAME3"], i, new_full_name2)
                MIT_ID_MAP[id]["FULL_NAME3"] = new_full_name2

            new_directory_full_name = new_full_name_fl
            if "MIDDLE_NAME" in MIT_ID_MAP[id]:
                new_directory_full_name = f"{new_lname}, {new_fname} {new_mname}."
            if "DIRECTORY_FULL_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["DIRECTORY_FULL_NAME"], i, new_directory_full_name)
                MIT_ID_MAP[id]["DIRECTORY_FULL_NAME"] = new_directory_full_name

            o_kerb = VMAP[table_name][table["KRB_NAME"]
                                      ][i][0] if "KRB_NAME" in table else ""
            kerb = random_kerb(new_fname, new_lname)
            KERB_MAP[o_kerb] = [kerb]
            if "KRB_NAME" in fill_fields:
                set_value_by_index(table_name, table["KRB_NAME"], i, kerb)
                MIT_ID_MAP[id]["KRB_NAME"] = kerb

            kerb_upper = kerb.upper()
            if "KRB_NAME_UPPERCASE" in fill_fields:
                set_value_by_index(
                    table_name, table["KRB_NAME_UPPERCASE"], i, kerb_upper)
                MIT_ID_MAP[id]["KRB_NAME_UPPERCASE"] = kerb.upper()

            email = f"{kerb}{random.choice(EMAIL_SUFFIX)}"
            if "EMAIL_ADDRESS" in fill_fields:
                domain = VMAP[table_name][table["EMAIL_ADDRESS"]
                                          ][i][0].split("@")[1].lower()
                new_domain = random.choice(EMAIL_SUFFIX)
                if domain in EMAIL_DOMAIN_MAP:
                    new_domain = EMAIL_DOMAIN_MAP[domain]
                EMAIL_DOMAIN_MAP[domain] = new_domain
                email = f"{kerb}{new_domain}"
                set_value_by_index(
                    table_name, table["EMAIL_ADDRESS"], i, email)
                MIT_ID_MAP[id]["EMAIL_ADDRESS"] = email
            KERB_MAP[o_kerb].append(email)

            email_upper = email.upper()
            if "EMAIL_ADDRESS_UPPERCASE" in fill_fields:
                set_value_by_index(
                    table_name, table["EMAIL_ADDRESS_UPPERCASE"], i, email_upper)
                MIT_ID_MAP[id]["EMAIL_ADDRESS_UPPERCASE"] = email_upper

            personal_url = f"{kerb}{random.choice(URL_SUFFIX)}"
            if random.randint(0, 1):
                personal_url = f"https://www.{personal_url}"
            else:
                personal_url = f"http://www.{personal_url}"
            if "PERSONAL_URL" in fill_fields:
                set_value_by_index(
                    table_name, table["PERSONAL_URL"], i, personal_url)
                MIT_ID_MAP[id]["PERSONAL_URL"] = personal_url

            if "NAME_KNOWN_BY" in fill_fields:
                set_value_by_index(
                    table_name, table["NAME_KNOWN_BY"], i, new_fname)
                MIT_ID_MAP[id]["NAME_KNOWN_BY"] = new_fname

            if "PREFERRED_FIRST_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["PREFERRED_FIRST_NAME"], i, new_fname)
                MIT_ID_MAP[id]["PREFERRED_FIRST_NAME"] = new_fname

            if "PREFERRED_FIRST_NAME_UPPER" in fill_fields:
                set_value_by_index(
                    table_name, table["PREFERRED_FIRST_NAME_UPPER"], i, new_fname.upper())
                MIT_ID_MAP[id]["PREFERRED_FIRST_NAME_UPPER"] = new_fname.upper()

            if "PREFERRED_LAST_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["PREFERRED_LAST_NAME"], i, new_lname)
                MIT_ID_MAP[id]["PREFERRED_LAST_NAME"] = new_lname

            if "PREFERRED_LAST_NAME_UPPER" in fill_fields:
                set_value_by_index(
                    table_name, table["PREFERRED_LAST_NAME_UPPER"], i, new_lname.upper())
                MIT_ID_MAP[id]["PREFERRED_LAST_NAME_UPPER"] = new_lname.upper()

            if "PREFERRED_MIDDLE_NAME" in fill_fields:
                set_value_by_index(
                    table_name, table["PREFERRED_MIDDLE_NAME"], i, new_mname)
                MIT_ID_MAP[id]["PREFERRED_MIDDLE_NAME"] = new_mname

            if "OFFICE_PHONE" in fill_fields:
                new_phone = "".join([str(random.randint(0, 9))
                                    for _ in range(10)])
                if VMAP[table_name][table["OFFICE_PHONE"]][i][0] in PHONE_MAP:
                    new_phone = PHONE_MAP[VMAP[table_name]
                                          [table["OFFICE_PHONE"]][i][0]]
                set_value_by_index(
                    table_name, table["OFFICE_PHONE"], i, new_phone)
                MIT_ID_MAP[id]["OFFICE_PHONE"] = new_phone


def room_task(source, related, skip=False, hist=False):
    if not skip:
        building_rooms = get_column(source, "BUILDING_ROOM")
        rooms = get_column(source, "ROOM")
        rkey = get_column(source, "FCLT_ROOM_KEY")
        floors = get_column(source, "FLOOR")
        fiscal_period = []
        if hist:
            fiscal_period = get_column(source, "FISCAL_PERIOD")
        for i, br in enumerate(building_rooms):
            BUILDING_AND_ROOM_POOL.add(br)
            building = br.split("-")[0]

            new_room = -1
            if rooms[i] in ROOM_MAP:
                new_room = ROOM_MAP[rooms[i]]
            else:
                new_room = random_room_for_building(building, floors[i])

            new_building_room = f"{building}-{new_room}"
            set_value_by_index(source, "FCLT_ROOM_KEY", i, new_building_room)
            set_value_by_index(source, "BUILDING_ROOM", i, new_building_room)
            set_value_by_index(source, "ROOM", i, new_room)
            set_value_by_index(source, "SPACE_ID", i,
                               f"{building}-{floors[i]}-{new_room}")
            if hist:
                set_value_by_index(
                    source, "FCLT_ROOM_HIST_KEY", i, f"{new_building_room}-{fiscal_period[i]}")
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
                    if not room:
                        continue
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
                    if not only_room:
                        continue
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
                    if not room:
                        continue
                    new_building_room = -1
                    building, _, new_room = random_room_consider_floor(room)
                    if not new_room:
                        new_building_room = f"{building}"
                    else:
                        new_building_room = f"{building}-{new_room}"
                    set_value_by_index(
                        table_name, table[field], i, new_building_room)
            if field == "ALL_ROOM":
                for i, all_room in enumerate(cols):
                    if not all_room:
                        continue
                    info = all_room.split("-")
                    room = f"{info[0]}-{'-'.join(info[2:])}"
                    floor = info[1]
                    new_building_room = -1
                    building, _, new_room = random_room_consider_floor(room)
                    if not new_room:
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
    areas = get_column(source, "DEPARTMENT_PHONE_AREA_CODE")
    numbers = get_column(source, "DEPARTMENT_PHONE_NUMBER")
    for i, info in enumerate(zip(areas, numbers)):
        area, number = info
        new_phone = "".join([str(random.randint(0, 9)) for _ in range(10)])
        if area + number in PHONE_MAP:
            new_phone = PHONE_MAP[area + number]
        else:
            PHONE_MAP[area + number] = new_phone
        if area:
            set_value_by_index(
                source, "DEPARTMENT_PHONE_AREA_CODE", i, new_phone[:3])
        if number:
            set_value_by_index(
                source, "DEPARTMENT_PHONE_NUMBER", i, new_phone[3:])


def meet_task(related):
    cols = []
    for table_name in related:
        cols.extend(get_column(table_name, "MEET_PLACE"))
    for locs in cols:
        if not locs:
            continue
        loc_list = locs.split(",")
        for loc_raw in loc_list:
            loc = loc_raw.strip()
            if loc not in RKEY_MAP:
                building, _, room = random_room_consider_floor(loc)
                if not room:
                    RKEY_MAP[loc] = f"{building}"
                else:
                    RKEY_MAP[loc] = f"{building}-{room}"
    for table_name in related:
        for i, locs in enumerate(get_column(table_name, "MEET_PLACE")):
            if not locs:
                continue
            loc_list = locs.split(",")
            new_locs = []
            for loc_raw in loc_list:
                loc = loc_raw.strip()
                new_locs.append(RKEY_MAP[loc])
            set_value_by_index(table_name, "MEET_PLACE", i, ",".join(new_locs))


def session_task(source, alt=None):
    colname = "SESSION_LOCATION" if not alt else alt
    locations = get_column(source, colname)
    for i, loc in enumerate(locations):
        if not loc:
            continue
        if "zoom" in loc.lower():
            new_loc = hide_zoom_id(loc, "zoom")
            set_value_by_index(source, colname, i, new_loc)


def zoom_link_task(infos):
    for table, col_name in infos:
        datas = get_column(table, col_name)
        for i, data in enumerate(datas):
            if not data:
                continue
            new_data = hide_zoom_id(data, "mit.zoom.us")
            set_value_by_index(table, col_name, i, new_data)


def subject_task(source):
    names = get_column(source, "PERSON_NAME")
    emails = get_column(source, "PERSON_EMAIL")
    locations = get_column(source, "PERSON_LOCATION")
    for i, info in enumerate(zip(names, emails, locations)):
        name, email, loc = info
        fname, lname = random.choice(FNAMES), random.choice(LNAMES)
        kerb = random_kerb(fname, lname)
        if name:
            set_value_by_index(source, "PERSON_NAME", i, f"{fname} {lname}")
        if email:
            domain = email.split("@")[1].lower()
            new_domain = random.choice(EMAIL_SUFFIX)
            if domain in EMAIL_DOMAIN_MAP:
                new_domain = EMAIL_DOMAIN_MAP[domain]
            EMAIL_DOMAIN_MAP[domain] = new_domain
            new_email = f"{kerb}{new_domain}"
            set_value_by_index(source, "PERSON_EMAIL", i, new_email)
        if loc:
            if loc in MEET_MAP:
                set_value_by_index(source, "PERSON_LOCATION", i, MEET_MAP[loc])
            else:
                loc = loc.split(" ")[0]
                # don't need to process if just a building
                if "-" in loc:
                    b, _, r = random_room_consider_floor(loc)
                    new_loc = f"{b}-{r}"
                    set_value_by_index(source, "PERSON_LOCATION", i, new_loc)

            # check weird bug
            if "[" in VMAP[source]["PERSON_LOCATION"][i][1]:
                print("ERROR:", VMAP[source]["PERSON_LOCATION"][i][1])


def library_task(related, name):
    keys = get_column(name, "LIBRARY_COURSE_INSTRUCTOR_KEY")
    lname_map = {}
    for i, key in enumerate(keys):
        fname, lname = random.choice(FNAMES), random.choice(LNAMES)
        new_name = f"{lname}, {fname}"
        set_value_by_index(name, "INSTRUCTOR_NAME", i, new_name)
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
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/'\".,")
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
    usages = get_column(source, "SPACE_USAGE")
    for i, usage in enumerate(usages):
        if usage:
            if usage not in USAGE_MAP:
                USAGE_MAP[usage] = random.choice(USAGES)
            set_value_by_index(source, "SPACE_USAGE", i, USAGE_MAP[usage])


def clamp_task(area, integers):
    return
    # for table_name, column in area.items():
    #     cols = get_column(table_name, column)
    #     for i, num in enumerate(cols):
    #         if num:
    #             val = random.uniform(float(num) * 0.95, float(num) * 1.05)
    #             if type(num) == str:
    #                 val = str(val)
    #             set_value_by_index(table_name, column, i, val)
    # for table_name, column in integers.items():
    #     cols = get_column(table_name, column)
    #     nums = [int(num) for num in cols if num and num == num]
    #     min_num, max_num = min(nums), max(nums)
    #     for i, num in enumerate(cols):
    #         if num:
    #             val = random.randint(min_num, max_num)
    #             val = round(val, -1)  # round to the nearest 10
    #             if type(num) == str:
    #                 val = str(val)
    #             set_value_by_index(table_name, column, i, val)


def title_task(title_cols):
    for tblcol in title_cols:
        table, col = tblcol
        titles = get_column(table, col)
        for i, title in enumerate(titles):
            if not title:
                continue
            new_title = random.choice(TITLES)
            if title in TITLE_MAP:
                new_title = TITLE_MAP[title]
            TITLE_MAP[title] = new_title
            set_value_by_index(table, col, i, new_title)


def robust_krb_task(related, cap=False):
    for table_name, column_name in related:
        krb_names = get_column(table_name, column_name)
        for i, krb in enumerate(krb_names):
            if not krb:
                continue
            is_email = "@" in krb
            split_ = krb.split("@")
            krb = split_[0]
            new_fname, new_lname = random.choice(FNAMES), random.choice(LNAMES)
            new_krb = random_kerb(new_fname, new_lname)
            domain = split_[1].lower() if is_email and len(
                split_) > 1 else "robust"
            new_domain = random.choice(EMAIL_SUFFIX)
            if domain in EMAIL_DOMAIN_MAP:
                new_domain = EMAIL_DOMAIN_MAP[domain]
            EMAIL_DOMAIN_MAP[domain] = new_domain
            new_email = f"{new_krb}{new_domain}"
            if krb in KERB_MAP:
                new_krb = KERB_MAP[krb][0]
                new_email = KERB_MAP[krb][1]
            KERB_MAP[krb] = [new_krb, new_email]
            if is_email:
                if cap:
                    new_email = new_email.upper()
                set_value_by_index(table_name, column_name, i, new_email)
            else:
                if cap:
                    new_krb = new_krb.upper()
                set_value_by_index(table_name, column_name, i, new_krb)


def responsible_task(infos):
    for table, id_col, name_col in infos:
        ids = get_column(table, id_col)
        names = get_column(table, name_col)
        for row_num, id_raw in enumerate(ids):
            if not names[row_num]:
                continue
            id = str(id_raw)
            if type(id_raw) == float and id_raw == id_raw:
                id = str(int(float(id)))
            id_list = [x.strip() for x in id.split(",")]
            new_ids = []
            new_names = []
            for id in id_list:
                if not id or id == "nan":
                    continue
                if id not in MIT_ID_MAP:
                    new_id = random_mitid()
                    MIT_ID_MAP[id] = {}
                    MIT_ID_MAP[id]["MIT_ID"] = new_id
                if "FULL_NAME_FL" not in MIT_ID_MAP[id]:
                    fname, lname = random.choice(FNAMES), random.choice(LNAMES)
                    MIT_ID_MAP[id]["FULL_NAME_FL"] = f"{lname}, {fname}"
                new_ids.append(MIT_ID_MAP[id]["MIT_ID"])
                new_names.append(MIT_ID_MAP[id]["FULL_NAME_FL"])
            set_value_by_index(table, id_col, row_num, ",".join(new_ids))
            set_value_by_index(table, name_col, row_num, ",".join(new_names))


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
            ["COURSE_CATALOG_SUBJECT_OFFERED", {
                "FULL_NAME2": "FALL_INSTRUCTORS",
                "FULL_NAME3": "SPRING_INSTRUCTORS",
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
        "func": zoom_link_task,
        "infos": [
            ["IAP_SUBJECT_SESSION", "SESSION_DESCRIPTION"],
        ]
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
    },
    {
        "func": title_task,
        "title_cols": [
            ["IAP_SUBJECT_PERSON", "PERSON_TITLE"],
            ["EMPLOYEE_DIRECTORY", "DIRECTORY_TITLE"],
            ["EMPLOYEE_DIRECTORY", "PRIMARY_TITLE"],
        ]
    },
    {
        "func": responsible_task,
        "infos": [
            ["LIBRARY_SUBJECT_OFFERED", "RESPONSIBLE_FACULTY_MIT_ID",
                "RESPONSIBLE_FACULTY_NAME"],
            ["COURSE_CATALOG_SUBJECT_OFFERED",
                "RESPONSIBLE_FACULTY_MIT_ID", "RESPONSIBLE_FACULTY_NAME"],
            ["TIP_SUBJECT_OFFERED", "RESPONSIBLE_FACULTY_MIT_ID",
                "RESPONSIBLE_FACULTY_NAME"],
            ["SUBJECT_OFFERED", "RESPONSIBLE_FACULTY_MIT_ID",
                "RESPONSIBLE_FACULTY_NAME"],
        ]
    },
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
# turn each table in VMAP into a 2d dataframe, then write it with the headers as a csv file

# turn each array of two elements in VMAP into a just the second element
VMAP = {table_name: {key: [val[1] for val in VMAP[table_name][key]]
                     for key in VMAP[table_name]} for table_name in VMAP}
for table_name in VMAP:
    df = pandas.DataFrame(VMAP[table_name])
    # write df to csv, make sure that we export with the right dtype, same as the original
    df.to_csv(f"redacted/{table_name}.csv", index=False)
    print("finished writing:", table_name)

VMAP = {}

TASKS = [
    [
        "FCLT_ROOMS_HIST",
        {
            "func": room_task,
            "source": "FCLT_ROOMS_HIST",
            "related": [],
            "skip": False,
            "hist": True,
        },
        {
            "func": clamp_task,
            "area": {
                "FCLT_ROOMS_HIST": "AREA",
            },
            "integers": {}
        },
    ],
    [
        "DRUPAL_COURSE_CATALOG",
        {
            "func": person_task,
            "related": [
                ["DRUPAL_COURSE_CATALOG", {
                    "FULL_NAME2": "FALL_INSTRUCTORS",
                    "FULL_NAME3": "SPRING_INSTRUCTORS",
                }],
            ]
        },
        {
            "func": responsible_task,
            "infos": [
                ["DRUPAL_COURSE_CATALOG", "RESPONSIBLE_FACULTY_MIT_ID",
                    "RESPONSIBLE_FACULTY_NAME"],
            ]
        },
        {
            "func": meet_task,
            "related": [
                "DRUPAL_COURSE_CATALOG",
            ]
        },
    ],
    [
        "SUBJECT_IAP_SCHEDULE",
        {
            "func": session_task,
            "source": "SUBJECT_IAP_SCHEDULE",
            "alt": "MEET_PLACE",
        },
        {
            "func": zoom_link_task,
            "infos": [
                ["SUBJECT_IAP_SCHEDULE", "REMARKS"],
            ]
        }
    ],
    [
        "WAREHOUSE_USERS",
        {
            "func": person_task,
            "related": [
                ["WAREHOUSE_USERS", {
                    "MIT_ID": "MIT_ID",
                    "KRB_NAME": "KRB_NAME",
                    "KRB_NAME_UPPERCASE": "KRB_NAME_UPPERCASE",
                    "LAST_NAME": "LAST_NAME",
                    "FIRST_NAME": "FIRST_NAME",
                    "MIDDLE_NAME": "MIDDLE_NAME",
                    "EMAIL_ADDRESS": "EMAIL_ADDRESS",
                    "OFFICE_PHONE": "OFFICE_PHONE",
                }],
            ]
        },
        {
            "func": room_task,
            "source": "",
            "related": [
                ["WAREHOUSE_USERS", {
                    "BUILDING_ROOM": "OFFICE_LOCATION"
                }],
            ],
            "skip": True,
        },
    ],
    [
        "DRUPAL_EMPLOYEE_DIRECTORY",
        {
            "func": person_task,
            "related": [
                ["DRUPAL_EMPLOYEE_DIRECTORY", {
                    "MIT_ID": "MIT_ID",
                    "FULL_NAME": "FULL_NAME",
                    "LAST_NAME": "LAST_NAME",
                    "FIRST_NAME": "FIRST_NAME",
                    "MIDDLE_NAME": "MIDDLE_NAME",
                    "EMAIL_ADDRESS": "EMAIL_ADDRESS",
                    "PERSONAL_URL": "PERSONAL_URL",
                    "OFFICE_PHONE": "OFFICE_PHONE",
                }],
            ]
        },
        {
            "func": room_task,
            "source": "",
            "related": [
                ["DRUPAL_EMPLOYEE_DIRECTORY", {
                    "BUILDING_ROOM": "OFFICE_LOCATION"
                }],
            ],
            "skip": True,
        },
        {
            "func": title_task,
            "title_cols": [
                ["DRUPAL_EMPLOYEE_DIRECTORY", "PRIMARY_TITLE"],
                ["DRUPAL_EMPLOYEE_DIRECTORY", "DIRECTORY_TITLE"],
            ]
        },
    ],
    [
        "SE_PERSON",
        {
            "func": person_task,
            "related": [
                ["SE_PERSON", {
                    "MIT_ID": "MIT_ID",
                    "KRB_NAME": "KRB_NAME",
                    "FULL_NAME": "FULL_NAME",
                    "LAST_NAME": "LAST_NAME",
                    "FIRST_NAME": "FIRST_NAME",
                    "MIDDLE_NAME": "MIDDLE_NAME",
                }],
            ]
        },
        {
            "func": room_task,
            "source": "",
            "related": [
                ["SE_PERSON", {
                    "BUILDING_ROOM": "OFFICE_LOCATION"
                }],
            ],
            "skip": True,
        },
    ],
    [
        "HR_FACULTY_ROSTER",
        {
            "func": person_task,
            "related": [
                ["HR_FACULTY_ROSTER", {
                    "MIT_ID": "MIT_ID",
                    "LAST_NAME": "LAST_NAME",
                    "FIRST_NAME": "FIRST_NAME",
                    "MIDDLE_NAME": "MIDDLE_NAME",
                }],
            ]
        },
        {
            "func": title_task,
            "title_cols": [
                ["HR_FACULTY_ROSTER", "ENDOWED_CHAIR"],
            ]
        }
    ],
    [
        "SUBJECT_SUMMARY",
        {
            "func": clamp_task,
            "area": {},
            "integers": {
                "SUBJECT_SUMMARY": "SUBJECT_ENROLLMENT_NUMBER",
                "SUBJECT_SUMMARY": "CLUSTER_ENROLLMENT_NUMBER",
            }
        },
    ],
    [
        "SUBJECT_OFFERED_SUMMARY",
        {
            "func": responsible_task,
            "infos": [
                ["SUBJECT_OFFERED_SUMMARY", "RESPONSIBLE_FACULTY_MIT_ID",
                    "RESPONSIBLE_FACULTY_NAME"]
            ],
        },
        {
            "func": clamp_task,
            "area": {},
            "integers": {
                "SUBJECT_OFFERED_SUMMARY": "SUBJECT_ENROLLMENT_NUMBER",
                "SUBJECT_OFFERED_SUMMARY": "CLUSTER_ENROLLMENT_NUMBER",
                "SUBJECT_OFFERED_SUMMARY": "NUM_ENROLLED_STUDENTS",
            }
        },
    ],
    [
        "FCLT_BUILDING_HIST_1",
        {
            "func": clamp_task,
            "area": {
                "FCLT_BUILDING_HIST_1": "EXT_GROSS_AREA",
                "FCLT_BUILDING_HIST_1": "ASSIGNABLE_AREA",
                "FCLT_BUILDING_HIST_1": "NON_ASSIGNABLE_AREA",
                "FCLT_BUILDING_HIST_1": "BUILDING_HEIGHT",
            },
            "integers": {
                "FCLT_BUILDING_HIST_1": "NUM_OF_ROOMS",
            }
        },
    ],
    [
        "FCLT_FLOOR",
        {
            "func": clamp_task,
            "area": {
                "FCLT_FLOOR": "EXT_GROSS_AREA",
                "FCLT_FLOOR": "ASSIGNABLE_AREA",
                "FCLT_FLOOR": "NON_ASSIGNABLE_AREA",
            },
            "integers": {}
        },
    ],
    [
        "FCLT_FLOOR_HIST",
        {
            "func": clamp_task,
            "area": {
                "FCLT_FLOOR_HIST": "EXT_GROSS_AREA",
                "FCLT_FLOOR_HIST": "ASSIGNABLE_AREA",
                "FCLT_FLOOR_HIST": "NON_ASSIGNABLE_AREA",
            },
            "integers": {}
        },
    ],
    [
        "ZPM_ROOMS_LOAD",
        {
            "func": room_task,
            "source": "",
            "related": [
                ["ZPM_ROOMS_LOAD", {
                    "BUILDING_ROOM": "BUILDING_ROOM"
                }],
            ],
            "skip": True,
        },
        {
            "func": usage_task,
            "source": "ZPM_ROOMS_LOAD",
        },
    ],
    [
        "MOIRA_LIST_DETAIL",
        {
            "func": robust_krb_task,
            "related": [
                ["MOIRA_LIST_DETAIL", "MOIRA_LIST_MEMBER"],
            ]
        }
    ],
    [
        "PERSON_AUTH_AREA",
        {
            "func": robust_krb_task,
            "related": [
                ["PERSON_AUTH_AREA", "USER_NAME"],
            ],
            "cap": True
        }
    ],
    [
        "ROLES_FIN_PA",
        {
            "func": robust_krb_task,
            "related": [
                ["ROLES_FIN_PA", "USERNAME"],
            ]
        }
    ],
    [
        "TABLES",
        {
            "func": robust_krb_task,
            "related": [
                ["TABLES", "BUSINESS_CONTACT_EMAIL"],
            ]
        }
    ],
]

print("\nStarting Phase 2\n")

for task_info in TASKS:
    table, tasks = task_info[0], task_info[1:]
    info = pandas.read_csv(f"data/{table}.csv", engine="pyarrow")
    headers = [h.strip('"') for h in info.columns]
    VMAP[table] = {header: [[x, x] for x in info[header].tolist()]
                   for header in headers}

    print("tasklist starting for table:", table)
    for task in tasks:
        print("\tstarting:", task["func"].__name__)

        args = []
        for key in task:
            if key != "func":
                args.append(task[key])
        task["func"](*args)

    VMAP = {table_name: {key: [val[1] for val in VMAP[table_name][key]]
                         for key in VMAP[table_name]} for table_name in VMAP}
    for table_name in VMAP:
        df = pandas.DataFrame(VMAP[table_name])
        df.to_csv(f"redacted/{table_name}.csv", index=False)
        print("finished writing:", table_name)

    VMAP = {}
