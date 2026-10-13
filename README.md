# ACEest Fitness & Gym — DevOps Assignment

A Flask REST API for ACEest Fitness & Gym, developed for Introduction to DevOps Assignment 1.

The application provides fitness-program information, calorie estimation, client profiles, progress tracking, workouts, body metrics, BMI calculation, membership management and program generation. SQLite is used for persistence.

The DevOps implementation covers Git/GitHub, Pytest, Flake8, Docker, GitHub Actions and Jenkins.

## Technology Stack

- Python 3
- Flask and SQLite
- Pytest and Flake8
- Docker and Gunicorn
- Git and GitHub
- GitHub Actions
- Jenkins

## Features

- Fat Loss (FL), Muscle Gain (MG) and Beginner (BG) programs.
- Calorie estimation based on the selected program.
- Client registration and retrieval.
- Weekly adherence tracking.
- Workout logging.
- Body metrics and BMI calculation.
- Membership status management.
- Fitness-program generation.
- Demo administrator login endpoint.
- Automated tests for API endpoints and validation.

## Project Structure

```text
ACEest_Fitness_and_Gym/
├── app.py
├── requirements.txt
├── pytest.ini
├── .flake8
├── .gitignore
├── .dockerignore
├── Dockerfile
├── Jenkinsfile
├── README.md
├── tests/
│   └── test_app.py
├── .github/
│   └── workflows/
│       └── main.yml
├── evidence/
└── Screenshots/
```

## Prerequisites

- Python 3 and pip
- Git
- Docker Engine
- A GitHub account
- Access to the Prayogshaala Rocky Linux lab
- Access to the configured Jenkins instance

## Local Setup

From the project root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

The Flask development server listens on port 5000 by default.

Check application health:

```bash
curl -fsS http://127.0.0.1:5000/health
```

Expected response:

```json
{"status":"UP"}
```

List the fitness programs:

```bash
curl -fsS http://127.0.0.1:5000/programs
```

The default SQLite database is `aceest_fitness.db` in the application directory. Set `ACEEST_DATABASE` to use another path.

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/programs` | List fitness programs |
| GET | `/programs/<code>` | Retrieve a program |
| GET, POST | `/clients` | List or create clients |
| GET | `/clients/<name>` | Retrieve a client |
| GET, POST | `/clients/<name>/progress` | Read or record weekly adherence |
| GET | `/clients/<name>/bmi` | Calculate a client's BMI |
| GET, POST | `/bmi` | Calculate BMI for a named client |
| GET, POST | `/workouts` | List or record workouts |
| GET, POST | `/metrics` | List or record body metrics |
| GET, POST | `/membership` | Read or update membership status |
| POST | `/generate-program` | Generate a fitness plan |
| POST | `/login` | Validate demo administrator credentials |

### Example: Create a client

```bash
curl -X POST http://127.0.0.1:5000/clients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ravi",
    "weight": 70,
    "height": 170,
    "program": "FL"
  }'
```

### Example: Calculate BMI

```bash
curl -fsS http://127.0.0.1:5000/clients/Ravi/bmi
```

Weights are in kilograms and heights are in centimetres.

## Testing and Code Quality

Run the test suite:

```bash
python -m pytest -v
```

Run the linter:

```bash
flake8 app.py tests/test_app.py
```

Check Python syntax:

```bash
python -m py_compile app.py tests/test_app.py
```

The current test suite contains 29 test cases covering application endpoints, business logic and input validation.

## Docker

Build the image:

```bash
docker build -t aceest-fitness:1.0 .
```

Start the application:

```bash
docker run -d \
  --name aceest-fitness \
  -p 5000:5000 \
  aceest-fitness:1.0
```

Verify the container:

```bash
docker ps --filter name=aceest-fitness
curl -fsS http://127.0.0.1:5000/health
```

Run tests inside the image:

```bash
docker run --rm aceest-fitness:1.0 pytest -q
```

Inspect application logs:

```bash
docker logs aceest-fitness
```

Stop and remove the container when finished:

```bash
docker rm -f aceest-fitness
```

The Docker image uses a slim Python base image and runs the application as a non-root user.

The default SQLite database inside a container is not automatically preserved when the container is removed. Use a persistent volume or a suitable backup process when application data must survive container replacement.

## Git and GitHub Workflow

The repository uses these branches:

- `main` — submission-ready code.
- `develop` — integration branch.
- `docs/*`, `feature/*` and `infra/*` — isolated changes.

Changes should use descriptive commit messages and be integrated through pull requests.

Repository:

https://github.com/Shankarguggi/ACEest-Fitness-and-Gym

## GitHub Actions

The intended workflow is defined in `.github/workflows/main.yml`.

The workflow must run on pushes and pull requests and execute:

1. Python syntax validation and Flake8 linting.
2. Docker image assembly.
3. Pytest execution inside the containerized environment.

Workflow results will be available in the GitHub repository's Actions tab after the workflow has been implemented and verified.

## Jenkins

The pipeline will be defined in the repository's `Jenkinsfile`.

Configure a Jenkins Pipeline job using **Pipeline script from SCM**:

- SCM: Git
- Repository: `git@github.com:Shankarguggi/ACEest-Fitness-and-Gym.git`
- Branch specifier: `*/main`
- Script path: `Jenkinsfile`

The Jenkins agent needs access to Git, Python 3 and the network resources required to install Python dependencies.

The planned build stages are checkout, environment setup, syntax validation, lint and automated tests. Jenkins build results can be inspected in Console Output.

These CI/CD descriptions document the planned configuration; successful pipeline execution must be verified separately.

## Demo Credentials and Security

The application defaults to username `admin` and password `admin` for classroom demonstration. The credentials can be configured through `ACEEST_ADMIN_USERNAME` and `ACEEST_ADMIN_PASSWORD`.

The default credentials are not suitable for production. Configure secure credentials and appropriate access controls before any real deployment.

Do not commit passwords, SSH private keys, API tokens, `.env` files, local databases or recovery backups.

## Evidence

The `evidence/` directory stores verification results generated during the lab exercise. The `Screenshots/` directory contains screenshots for project documentation.

Keep project files and evidence under `~/workspace` in Prayogshaala because files outside that workspace may be deleted when the VM shuts down.

## Assignment Scope

This project demonstrates application development, version control, automated testing, Docker containerization and CI/CD build validation for ACEest Fitness & Gym.

The final submission should include the working application, tests, Dockerfile, GitHub Actions workflow, Jenkinsfile and this README, hosted in the required public GitHub repository.
