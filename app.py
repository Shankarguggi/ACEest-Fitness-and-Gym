
"""ACEest Fitness & Gym REST API."""

import os

import random

import sqlite3

from datetime import date

from pathlib import Path


from flask import Flask, current_app, g, jsonify, request

from werkzeug.security import check_password_hash, generate_password_hash


ROOT = Path(__file__).resolve().parent

DB_DEFAULT = os.environ.get("ACEEST_DATABASE", str(ROOT / "aceest_fitness.db"))


PROGRAMS = {

    "FL": {

        "code": "FL",

        "name": "Fat Loss (FL)",

        "calorie_factor": 22,

        "workout": "Squat + core, interval bike, bench press, deadlift, Zone 2 cardio",

        "diet": "Egg whites and oats; grilled chicken and brown rice; fish curry and millet roti",

    },

    "MG": {

        "code": "MG",

        "name": "Muscle Gain (MG)",

        "calorie_factor": 35,

        "workout": "Squat, bench press, deadlift, front squat, incline press, barbell rows",

        "diet": "Eggs and peanut-butter oats; chicken biryani; mutton curry and rice",

    },

    "BG": {

        "code": "BG",

        "name": "Beginner (BG)",

        "calorie_factor": 26,

        "workout": "Full-body circuit: air squats, ring rows and push-ups",

        "diet": "Balanced meals including idli, dosa, rice and dal",

    },

}


ALIASES = {

    key: code

    for code, item in PROGRAMS.items()

    for key in (

        code,

        item["name"].upper(),

        item["name"].split(" (")[0].upper(),

    )

}


PLANS = {

    "FL": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],

    "MG": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],

    "BG": ["Full Body 3x/week", "Light Strength + Mobility"],

}


SCHEMA = """

CREATE TABLE IF NOT EXISTS users (

    username TEXT PRIMARY KEY,

    password_hash TEXT NOT NULL,

    role TEXT NOT NULL DEFAULT 'Admin'

);

CREATE TABLE IF NOT EXISTS clients (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE,

    age INTEGER,

    height REAL,

    weight REAL NOT NULL,

    program_code TEXT NOT NULL,

    calories INTEGER NOT NULL,

    target_weight REAL,

    target_adherence INTEGER NOT NULL DEFAULT 80,

    membership_status TEXT NOT NULL DEFAULT 'Active',

    membership_end TEXT,

    program_plan TEXT,

    coach_notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

);

CREATE TABLE IF NOT EXISTS progress (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    client_name TEXT NOT NULL,

    week TEXT NOT NULL,

    adherence INTEGER NOT NULL CHECK(adherence BETWEEN 0 AND 100),

    UNIQUE(client_name, week),

    FOREIGN KEY(client_name) REFERENCES clients(name) ON DELETE CASCADE

);

CREATE TABLE IF NOT EXISTS workouts (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    client_name TEXT NOT NULL,

    date TEXT NOT NULL,

    workout_type TEXT NOT NULL,

    duration_min INTEGER NOT NULL CHECK(duration_min > 0),

    notes TEXT NOT NULL DEFAULT '',

    FOREIGN KEY(client_name) REFERENCES clients(name) ON DELETE CASCADE

);

CREATE TABLE IF NOT EXISTS metrics (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    client_name TEXT NOT NULL,

    date TEXT NOT NULL,

    weight REAL NOT NULL CHECK(weight > 0),

    waist REAL,

    bodyfat REAL,

    FOREIGN KEY(client_name) REFERENCES clients(name) ON DELETE CASCADE

);

"""


def normalize_program(value):
    """Accept FL/MG/BG or the corresponding program display name."""

    if not isinstance(value, str) or value.strip().upper() not in ALIASES:

        raise ValueError("program must be FL, MG or BG")

    return ALIASES[value.strip().upper()]


def calculate_calories(weight, program):
    """Use the calorie factors defined by the supplied ACEest baseline."""

    weight = float(weight)

    if weight <= 0:

        raise ValueError("weight must be greater than zero")

    return int(weight * PROGRAMS[normalize_program(program)]["calorie_factor"])


def get_db():
    """Maintain one SQLite connection for each application context."""

    if "db" not in g:

        path = current_app.config["DATABASE"]

        if path != ":memory:":

            Path(path).expanduser().resolve().parent.mkdir(

                parents=True, exist_ok=True

            )

        g.db = sqlite3.connect(path)

        g.db.row_factory = sqlite3.Row

        g.db.execute("PRAGMA foreign_keys=ON")

    return g.db


def close_db(_error=None):

    db = g.pop("db", None)

    if db is not None:

        db.close()


def body_json():

    value = request.get_json(silent=True)

    return value if isinstance(value, dict) else None


def client_row(name):

    return get_db().execute(

        "SELECT * FROM clients WHERE name=?", (name,)

    ).fetchone()


def client_dict(row):

    item = dict(row)

    item["program"] = item.pop("program_code")

    return item


def is_date(value):

    try:

        return date.fromisoformat(value).isoformat()

    except (TypeError, ValueError) as exc:

        raise ValueError("date must use YYYY-MM-DD format") from exc


def create_app(test_config=None):

    app = Flask(__name__)

    app.config.update(DATABASE=DB_DEFAULT, TESTING=False)

    if test_config:

        app.config.update(test_config)

    app.teardown_appcontext(close_db)

    with app.app_context():

        db = get_db()

        db.executescript(SCHEMA)

        # Demo credentials only; configure a different password outside class demos.

        username = os.environ.get("ACEEST_ADMIN_USERNAME", "admin")

        password = os.environ.get("ACEEST_ADMIN_PASSWORD", "admin")

        db.execute(
            """INSERT OR IGNORE INTO users
               (username, password_hash, role) VALUES (?, ?, ?)""",
            (username, generate_password_hash(password), "Admin"),
        )
        db.commit()

    @app.get("/")
    def home():

        return jsonify(

            application="ACEest Fitness & Gym API",

            version="1.0.0",

            endpoints=[

                "/health", "/programs", "/clients", "/workouts",

                "/metrics", "/membership", "/generate-program", "/login",

            ],

        )

    @app.get("/health")
    def health():

        return jsonify(status="UP")

    @app.get("/programs")
    def programs():

        return jsonify(programs=list(PROGRAMS.values()))

    @app.get("/programs/<code>")
    def program(code):

        try:

            return jsonify(PROGRAMS[normalize_program(code)])

        except ValueError as exc:

            return jsonify(error=str(exc)), 404

    @app.route("/clients", methods=["GET", "POST"])
    def clients():

        db = get_db()

        if request.method == "GET":

            rows = db.execute(

                "SELECT * FROM clients ORDER BY name"

            ).fetchall()

            return jsonify(clients=[client_dict(row) for row in rows])

        data = body_json()

        if data is None:

            return jsonify(error="Request body must be a JSON object"), 400

        name = data.get("name")

        if not isinstance(name, str) or not name.strip():

            return jsonify(error="name is required"), 400

        try:

            code = normalize_program(data.get("program"))

            weight = float(data.get("weight"))

            calories = calculate_calories(weight, code)

            age = int(data["age"]) if data.get("age") is not None else None

            height = (

                float(data["height"])

                if data.get("height") is not None

                else None

            )

            target_weight = (

                float(data["target_weight"])

                if data.get("target_weight") is not None

                else None

            )

            adherence = int(data.get("target_adherence", 80))

            if age is not None and age <= 0:

                raise ValueError("age must be greater than zero")

            if height is not None and height <= 0:

                raise ValueError("height must be greater than zero")

            if target_weight is not None and target_weight <= 0:

                raise ValueError("target_weight must be greater than zero")

            if not 0 <= adherence <= 100:

                raise ValueError("target_adherence must be between 0 and 100")

        except (TypeError, ValueError) as exc:

            return jsonify(error=str(exc)), 400

        try:

            db.execute(

                """INSERT INTO clients

                (name, age, height, weight, program_code, calories, target_weight,

                 target_adherence, membership_status, membership_end, coach_notes)

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",

                (

                    name.strip(), age, height, weight, code, calories,

                    target_weight, adherence, data.get("membership_status", "Active"),

                    data.get("membership_end"), str(data.get("coach_notes", "")),

                ),

            )

            db.commit()

        except sqlite3.IntegrityError:

            return jsonify(error="A client with that name already exists"), 409

        return jsonify(client=client_dict(client_row(name.strip()))), 201

    @app.get("/clients/<name>")
    def client_detail(name):

        row = client_row(name)

        if row is None:

            return jsonify(error="Client not found"), 404

        return jsonify(client=client_dict(row))

    @app.route("/clients/<name>/progress", methods=["GET", "POST"])
    def progress(name):

        if client_row(name) is None:

            return jsonify(error="Client not found"), 404

        db = get_db()

        if request.method == "GET":

            rows = db.execute(

                """SELECT week, adherence FROM progress

                   WHERE client_name=? ORDER BY week""",

                (name,),

            ).fetchall()

            return jsonify(

                client_name=name, progress=[dict(row) for row in rows]

            )

        data = body_json()

        if (

            data is None

            or not isinstance(data.get("week"), str)

            or not data["week"].strip()

        ):

            return jsonify(error="JSON week and adherence are required"), 400

        try:

            adherence = int(data.get("adherence"))

            if not 0 <= adherence <= 100:

                raise ValueError

        except (TypeError, ValueError):

            return jsonify(

                error="adherence must be an integer from 0 to 100"

            ), 400

        db.execute(

            """INSERT INTO progress(client_name, week, adherence) VALUES(?, ?, ?)

               ON CONFLICT(client_name, week)

               DO UPDATE SET adherence=excluded.adherence""",

            (name, data["week"].strip(), adherence),

        )

        db.commit()

        return jsonify(

            client_name=name, week=data["week"].strip(), adherence=adherence

        ), 201

    def bmi_result(name):

        row = client_row(name)

        if row is None:

            return jsonify(error="Client not found"), 404

        if not row["height"] or row["height"] <= 0:

            return jsonify(

                error="Client height is required to calculate BMI"

            ), 400

        bmi_value = row["weight"] / ((row["height"] / 100) ** 2)

        if bmi_value < 18.5:

            category = "Underweight"

        elif bmi_value < 25:

            category = "Normal"

        elif bmi_value < 30:

            category = "Overweight"

        else:

            category = "Obese"

        return jsonify(

            client_name=name, bmi=round(bmi_value, 1), category=category

        )

    @app.get("/clients/<name>/bmi")
    def client_bmi(name):

        return bmi_result(name)

    @app.route("/bmi", methods=["GET", "POST"])
    def bmi():

        data = body_json() if request.method == "POST" else {}

        name = (data or {}).get("name") or request.args.get("name")

        if not name:

            return jsonify(error="Provide a client name"), 400

        return bmi_result(name)

    @app.route("/workouts", methods=["GET", "POST"])
    def workouts():

        db = get_db()

        if request.method == "GET":

            name = request.args.get("client_name")

            if name:

                rows = db.execute(

                    "SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC",

                    (name,),

                ).fetchall()

            else:

                rows = db.execute(

                    "SELECT * FROM workouts ORDER BY date DESC"

                ).fetchall()

            return jsonify(workouts=[dict(row) for row in rows])

        data = body_json()

        if data is None:

            return jsonify(error="Request body must be a JSON object"), 400

        name = data.get("client_name")

        kind = data.get("workout_type")

        if (

            not isinstance(name, str) or not name.strip()

            or not isinstance(kind, str) or not kind.strip()

        ):

            return jsonify(error="client_name and workout_type are required"), 400

        if client_row(name.strip()) is None:

            return jsonify(error="Client not found"), 404

        try:

            duration = int(data.get("duration_min"))

            if duration <= 0:

                raise ValueError("duration_min must be positive")

            workout_date = is_date(data.get("date", date.today().isoformat()))

        except (TypeError, ValueError) as exc:

            return jsonify(error=str(exc) or "Invalid workout details"), 400

        cursor = db.execute(

            """INSERT INTO workouts

               (client_name, date, workout_type, duration_min, notes)

               VALUES (?, ?, ?, ?, ?)""",

            (

                name.strip(), workout_date, kind.strip(), duration,

                str(data.get("notes", "")),

            ),

        )

        db.commit()

        row = db.execute(

            "SELECT * FROM workouts WHERE id=?", (cursor.lastrowid,)

        ).fetchone()

        return jsonify(workout=dict(row)), 201

    @app.route("/metrics", methods=["GET", "POST"])
    def metrics():

        db = get_db()

        if request.method == "GET":

            name = request.args.get("client_name")

            if name:

                rows = db.execute(

                    "SELECT * FROM metrics WHERE client_name=? ORDER BY date DESC",

                    (name,),

                ).fetchall()

            else:

                rows = db.execute(

                    "SELECT * FROM metrics ORDER BY date DESC"

                ).fetchall()

            return jsonify(metrics=[dict(row) for row in rows])

        data = body_json()

        if data is None:

            return jsonify(error="Request body must be a JSON object"), 400

        name = data.get("client_name")

        if not isinstance(name, str) or not name.strip():

            return jsonify(error="client_name is required"), 400

        if client_row(name.strip()) is None:

            return jsonify(error="Client not found"), 404

        try:

            weight = float(data.get("weight"))

            waist = float(data["waist"]) if data.get("waist") is not None else None

            bodyfat = (

                float(data["bodyfat"])

                if data.get("bodyfat") is not None

                else None

            )

            if weight <= 0 or (waist is not None and waist <= 0):

                raise ValueError("weight and waist must be greater than zero")

            if bodyfat is not None and not 0 <= bodyfat <= 100:

                raise ValueError("bodyfat must be between 0 and 100")

            metric_date = is_date(data.get("date", date.today().isoformat()))

        except (TypeError, ValueError) as exc:

            return jsonify(error=str(exc) or "Invalid metric values"), 400

        cursor = db.execute(

            """INSERT INTO metrics

               (client_name, date, weight, waist, bodyfat)

               VALUES (?, ?, ?, ?, ?)""",

            (name.strip(), metric_date, weight, waist, bodyfat),

        )

        db.commit()

        row = db.execute(

            "SELECT * FROM metrics WHERE id=?", (cursor.lastrowid,)

        ).fetchone()

        return jsonify(metric=dict(row)), 201

    @app.route("/membership", methods=["GET", "POST"])
    def membership():

        db = get_db()

        if request.method == "GET":

            name = request.args.get("client_name")

            query = (

                "SELECT name AS client_name, membership_status, membership_end "

                "FROM clients"

            )

            if name:

                row = db.execute(query + " WHERE name=?", (name,)).fetchone()

                if row is None:

                    return jsonify(error="Client not found"), 404

                return jsonify(membership=dict(row))

            rows = db.execute(query + " ORDER BY name").fetchall()

            return jsonify(memberships=[dict(row) for row in rows])

        data = body_json()

        if data is None:

            return jsonify(error="Request body must be a JSON object"), 400

        name = data.get("client_name")

        status = data.get("membership_status")

        if not isinstance(name, str) or not name.strip():

            return jsonify(error="client_name is required"), 400

        if client_row(name.strip()) is None:

            return jsonify(error="Client not found"), 404

        if status not in {"Active", "Inactive", "Expired", "Cancelled"}:

            return jsonify(error="Invalid membership_status"), 400

        end = data.get("membership_end")

        try:

            end = is_date(end) if end else None

        except ValueError as exc:

            return jsonify(error=str(exc)), 400

        db.execute(

            """UPDATE clients SET membership_status=?, membership_end=?

               WHERE name=?""",

            (status, end, name.strip()),

        )

        db.commit()

        return jsonify(

            client_name=name.strip(), membership_status=status, membership_end=end

        )

    @app.post("/generate-program")
    def generate_program():

        data = body_json()

        name = data.get("client_name") if data else None

        if not isinstance(name, str) or not name.strip():

            return jsonify(error="client_name is required"), 400

        row = client_row(name.strip())

        if row is None:

            return jsonify(error="Client not found"), 404

        try:

            code = normalize_program(data.get("program", row["program_code"]))

        except ValueError as exc:

            return jsonify(error=str(exc)), 400

        plan = random.choice(PLANS[code])

        calories = calculate_calories(row["weight"], code)

        get_db().execute(

            """UPDATE clients SET program_code=?, calories=?, program_plan=?

               WHERE name=?""",

            (code, calories, plan, name.strip()),

        )

        get_db().commit()

        return jsonify(

            client_name=name.strip(),

            program=PROGRAMS[code]["name"],

            program_code=code,

            generated_plan=plan,

            estimated_calories=calories,

        )

    @app.post("/login")
    def login():

        data = body_json()

        if (

            not data

            or not isinstance(data.get("username"), str)

            or not isinstance(data.get("password"), str)

        ):

            return jsonify(error="username and password are required"), 400

        row = get_db().execute(

            "SELECT username, password_hash, role FROM users WHERE username=?",

            (data["username"],),

        ).fetchone()

        if row is None or not check_password_hash(row["password_hash"], data["password"]):

            return jsonify(error="Invalid credentials", authenticated=False), 401

        return jsonify(

            authenticated=True, username=row["username"], role=row["role"]

        )

    return app


app = create_app()


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
