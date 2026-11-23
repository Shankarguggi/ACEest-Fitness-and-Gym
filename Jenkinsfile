
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
                    python3 --version
                    git --version
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                    .venv/bin/python -m py_compile app.py tests/test_app.py
                    .venv/bin/flake8 app.py tests/test_app.py
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '.venv/bin/python -m pytest -v'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=aceest-fitness \
                              -Dsonar.projectName='ACEest Fitness and Gym' \
                              -Dsonar.sources=app.py \
                              -Dsonar.tests=tests \
                              -Dsonar.python.version=3.9 \
                              -Dsonar.sourceEncoding=UTF-8
                        """
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }

    post {
        success {
            echo 'Jenkins build, tests and SonarQube Quality Gate passed.'
        }
        failure {
            echo 'Pipeline failed. Review the stage logs.'
        }
        always {
            deleteDir()
        }
    }
}
