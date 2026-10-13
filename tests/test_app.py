
"""Tests for the ACEest Fitness & Gym API."""

import pytest


from app import calculate_calories, create_app


@pytest.fixture
def app(tmp_path):
    """Create an isolated application and database for each test."""

    application = create_app({

        "TESTING": True,

        "DATABASE": str(tmp_path / "test.db"),

    })

    yield application


@pytest.fixture
def client(app):
    """Provide Flask's test client."""

    with app.test_client() as test_client:

        yield test_client


def add_client(client, name="Ravi", weight=70, program="FL", height=170):
    """Create a client using the public API."""

    return client.post(

        "/clients",

        json={

            "name": name,

            "weight": weight,

            "program": program,

            "height": height,

        },

    )


def test_home_page(client):

    response = client.get("/")

    assert response.status_code == 200

    assert response.json["application"] == "ACEest Fitness & Gym API"


def test_health_endpoint(client):

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json["status"] == "UP"


def test_list_programs(client):

    response = client.get("/programs")

    assert response.status_code == 200

    assert {item["code"] for item in response.json["programs"]} == {

        "FL", "MG", "BG"

    }


def test_get_program_by_code(client):

    response = client.get("/programs/FL")

    assert response.status_code == 200

    assert response.json["calorie_factor"] == 22


def test_get_program_by_name(client):

    response = client.get("/programs/Fat%20Loss")

    assert response.status_code == 200

    assert response.json["code"] == "FL"


def test_unknown_program_returns_404(client):

    response = client.get("/programs/UNKNOWN")

    assert response.status_code == 404


def test_calculate_calories_for_fat_loss():

    assert calculate_calories(70, "FL") == 1540


def test_calorie_calculation_rejects_zero_weight():

    with pytest.raises(ValueError):

        calculate_calories(0, "FL")


def test_calorie_calculation_rejects_invalid_program():

    with pytest.raises(ValueError):

        calculate_calories(70, "UNKNOWN")


def test_create_client(client):

    response = add_client(client)

    assert response.status_code == 201

    assert response.json["client"]["name"] == "Ravi"

    assert response.json["client"]["calories"] == 1540

    assert response.json["client"]["program"] == "FL"


def test_create_client_requires_name(client):

    response = client.post(

        "/clients",

        json={"weight": 70, "program": "FL"},

    )

    assert response.status_code == 400


def test_create_client_rejects_invalid_program(client):

    response = add_client(client, program="UNKNOWN")

    assert response.status_code == 400


def test_create_client_rejects_invalid_weight(client):

    response = add_client(client, weight=0)

    assert response.status_code == 400


def test_duplicate_client_returns_conflict(client):

    assert add_client(client).status_code == 201

    response = add_client(client)

    assert response.status_code == 409


def test_list_clients(client):

    add_client(client)

    response = client.get("/clients")

    assert response.status_code == 200

    assert len(response.json["clients"]) == 1


def test_unknown_client_returns_404(client):

    response = client.get("/clients/Unknown")

    assert response.status_code == 404


def test_record_and_read_progress(client):

    add_client(client)

    response = client.post(

        "/clients/Ravi/progress",

        json={"week": "2026-W42", "adherence": 90},

    )

    assert response.status_code == 201

    response = client.get("/clients/Ravi/progress")

    assert response.status_code == 200

    assert response.json["progress"][0]["adherence"] == 90


def test_progress_rejects_invalid_adherence(client):

    add_client(client)

    response = client.post(

        "/clients/Ravi/progress",

        json={"week": "2026-W42", "adherence": 150},

    )

    assert response.status_code == 400


def test_bmi_calculation(client):

    add_client(client, weight=66, height=170)

    response = client.get("/clients/Ravi/bmi")

    assert response.status_code == 200

    assert response.json["bmi"] == 22.8

    assert response.json["category"] == "Normal"


def test_bmi_requires_height(client):

    response = client.post(

        "/clients",

        json={"name": "NoHeight", "weight": 70, "program": "FL"},

    )

    assert response.status_code == 201

    response = client.get("/clients/NoHeight/bmi")

    assert response.status_code == 400


def test_bmi_unknown_client_returns_404(client):

    response = client.get("/clients/Unknown/bmi")

    assert response.status_code == 404


def test_create_and_list_workout(client):

    add_client(client)

    response = client.post(

        "/workouts",

        json={

            "client_name": "Ravi",

            "date": "2026-10-13",

            "workout_type": "Strength Training",

            "duration_min": 45,

        },

    )

    assert response.status_code == 201

    assert response.json["workout"]["duration_min"] == 45

    response = client.get("/workouts?client_name=Ravi")

    assert response.status_code == 200

    assert len(response.json["workouts"]) == 1


def test_workout_rejects_unknown_client(client):

    response = client.post(

        "/workouts",

        json={

            "client_name": "Unknown",

            "workout_type": "Running",

            "duration_min": 30,

        },

    )

    assert response.status_code == 404


def test_create_and_list_body_metrics(client):

    add_client(client)

    response = client.post(

        "/metrics",

        json={

            "client_name": "Ravi",

            "date": "2026-10-13",

            "weight": 69.5,

            "waist": 80,

            "bodyfat": 18.5,

        },

    )

    assert response.status_code == 201

    assert response.json["metric"]["weight"] == 69.5

    response = client.get("/metrics?client_name=Ravi")

    assert response.status_code == 200

    assert len(response.json["metrics"]) == 1


def test_metrics_reject_invalid_bodyfat(client):

    add_client(client)

    response = client.post(

        "/metrics",

        json={

            "client_name": "Ravi",

            "weight": 69,

            "bodyfat": 150,

        },

    )

    assert response.status_code == 400


def test_update_membership(client):

    add_client(client)

    response = client.post(

        "/membership",

        json={

            "client_name": "Ravi",

            "membership_status": "Inactive",

        },

    )

    assert response.status_code == 200

    response = client.get("/membership?client_name=Ravi")

    assert response.status_code == 200

    assert response.json["membership"]["membership_status"] == "Inactive"


def test_generate_program(client):

    add_client(client)

    response = client.post(

        "/generate-program",

        json={"client_name": "Ravi", "program": "MG"},

    )

    assert response.status_code == 200

    assert response.json["program_code"] == "MG"

    assert response.json["generated_plan"]


def test_login_success(client):

    response = client.post(

        "/login",

        json={"username": "admin", "password": "admin"},

    )

    assert response.status_code == 200

    assert response.json["authenticated"] is True


def test_login_rejects_invalid_password(client):

    response = client.post(

        "/login",

        json={"username": "admin", "password": "wrong"},

    )

    assert response.status_code == 401

    assert response.json["authenticated"] is False
