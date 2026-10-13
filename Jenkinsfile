pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Build & Lint') {
            steps {
                sh '''
                    set -eu

                    echo "Python version:"
                    python3 --version

                    echo "Git version:"
                    git --version

                    echo "Creating a clean Python environment:"
                    python3 -m venv .venv

                    echo "Installing dependencies:"
                    .venv/bin/python -m pip install -r requirements.txt

                    echo "Checking syntax:"
                    .venv/bin/python -m py_compile app.py tests/test_app.py

                    echo "Running Flake8:"
                    .venv/bin/flake8 app.py tests/test_app.py
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '.venv/bin/python -m pytest -v'
            }
        }
    }

    post {
        success {
            echo 'Jenkins build and test stages passed.'
        }

        failure {
            echo 'Jenkins pipeline failed. Review the stage logs.'
        }

        always {
            deleteDir()
        }
    }
}
