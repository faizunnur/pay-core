// PayCore delivery pipeline — introduced in Week 2.
//
// Five stages, in the order the release flow actually happens:
//   Lint -> Test -> Security gate -> Build -> Publish the artifact
//
// Cheap checks first. The Build stage only runs if everything before it passed,
// because there is no point paying for a Docker build of code that fails lint.
//
// This pipeline BUILDS and VERIFIES. It does not deploy. A human decides to
// deploy, because that is the release engineer's call, not the pipeline's.

pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        IMAGE_NAME = 'paycore'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
        // Findings the team has reviewed and accepted, one id per line, with a
        // written justification. Empty to begin with — you fill it in Lab 5.
        AUDIT_EXCEPTIONS = 'ci/audit-exceptions.txt'
    }

    stages {

        stage('Lint') {
            steps {
                echo 'ruff — style and common bug patterns'
                sh 'ruff check .'
            }
        }

        stage('Test') {
            steps {
                echo 'pytest — the suite runs on SQLite, so it needs no database'
                sh 'pytest -q'
            }
        }

        stage('Security gate') {
            steps {
                echo 'pip-audit — known vulnerabilities in our dependencies'
                sh '''
                    set -eu
                    IGNORE=""
                    if [ -s "${AUDIT_EXCEPTIONS}" ]; then
                        # Every non-blank, non-comment line is an accepted finding.
                        for id in $(grep -vE '^[[:space:]]*(#|$)' "${AUDIT_EXCEPTIONS}" | awk '{print $1}'); do
                            IGNORE="${IGNORE} --ignore-vuln ${id}"
                        done
                    fi
                    echo "accepted exceptions:${IGNORE:- none}"
                    pip-audit -r requirements.txt --progress-spinner off ${IGNORE}
                '''
            }
            post {
                failure {
                    echo '''
                    ================================================================
                    SECURITY GATE FAILED.

                    This is the gate doing its job, not a broken build. Read the
                    findings above, then decide — as a team — for each one:

                      * FIX      the dependency is upgradeable and the cost is low
                      * ACCEPT   not exploitable in PayCore's context; record it in
                                 ci/audit-exceptions.txt with a justification and
                                 a review date
                      * BLOCK    exploitable here; this release does not ship

                    "Delete the gate" is not on the list.
                    ================================================================
                    '''.stripIndent()
                }
            }
        }

        stage('Build') {
            steps {
                echo "building ${IMAGE_NAME}:${IMAGE_TAG}"
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }

        stage('Publish the artifact') {
            steps {
                // Tagging is how a build becomes a candidate. Deploying it is a
                // separate, human decision — see Lab 6.
                sh '''
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:candidate
                    docker image ls ${IMAGE_NAME}
                '''
                echo "Candidate ready: ${IMAGE_NAME}:${IMAGE_TAG} (also tagged :candidate)"
            }
        }
    }

    post {
        success {
            echo "Build ${env.BUILD_NUMBER} passed every gate. It is a release candidate."
        }
        failure {
            echo "Build ${env.BUILD_NUMBER} failed. Read the FIRST error, not the last."
        }
    }
}
