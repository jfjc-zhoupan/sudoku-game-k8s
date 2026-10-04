pipeline {
    agent any

    environment {
        APP_NAME = 'sudoku-game'
        APP_DIR = 'app'
        VERSION_FILE = "${APP_DIR}/version.py"

        ACR_SERVER = 'acrsudokugame.azurecr.io'
        DOCKER_IMAGE = "${ACR_SERVER}/${APP_NAME}"

        AKS_RESOURCE_GROUP = 'rg-sudoku-game'
        AKS_CLUSTER_NAME = 'aks-sudoku-game'
        K8S_NAMESPACE = 'sudoku-game'
        K8S_MANIFESTS_DIR = 'k8s/aks'

        ORIGINAL_VERSION = ''
        NEW_VERSION = ''
        APP_PUBLIC_IP = ''
    }

    stages {
        stage("Checkout"){
            steps{
                deleteDir()
                checkout scm
                script {
                    echo "Branch: ${env.BRANCH_NAME}"
                    sh 'ls -la'
                    sh 'ls -la app/'
                    env.GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    echo "Commit SHA: ${env.GIT_COMMIT_SHORT}"
                }
            }
        }
        stage("Bump Version"){
            steps{
                script{
                    def versionContent = readFile("${env.VERSION_FILE}")
                    def versionLine = versionContent.readLines().find { line ->
                        line.trim().startsWith('__version__')
                    }
                    if (versionLine == null) {
                        error "Could not find __version__ in ${env.VERSION_FILE}"
                    }
                    def parts = versionLine.split('=')
                    def originalVersion = parts[1].trim().replace('"', '').replace("'", '')
                    def versionParts = originalVersion.split('\\.')
                    def newPatch = (versionParts[2] as Integer) + 1
                    def newVersion = "${versionParts[0]}.${versionParts[1]}.${newPatch}"

                    env.ORIGINAL_VERSION = originalVersion
                    env.NEW_VERSION = newVersion

                    echo "Original version: ${originalVersion}"
                    echo "New version: ${newVersion}"

                    sh """
                        sed -i 's/__version__ = .*/__version__ = "${newVersion}"/' ${env.VERSION_FILE}
                        grep __version__ ${env.VERSION_FILE}
                    """
                }
            }
        }
        stage("Build and Push Image"){
            steps{
                script{
                    def versionContent = readFile("${env.VERSION_FILE}")
                    def versionLine = versionContent.readLines().find { line ->
                        line.trim().startsWith('__version__')
                    }
                    def currentVersion = versionLine.split('=')[1].trim().replace('"', '').replace("'", '')
                    echo "Using version: ${currentVersion}"

                    withCredentials([usernamePassword(
                                credentialsId: 'acr-credentials',
                                usernameVariable: 'ACR_USER',
                                passwordVariable: 'ACR_PASS'
                            )]) {
                        sh """
                            echo "${ACR_PASS}" | docker login ${env.ACR_SERVER} -u "${ACR_USER}" --password-stdin
                            cd ${env.APP_DIR}
                            docker build -t ${env.DOCKER_IMAGE}:${currentVersion} .
                            docker tag ${env.DOCKER_IMAGE}:${currentVersion} ${env.DOCKER_IMAGE}:latest

                            docker push ${env.DOCKER_IMAGE}:${currentVersion}
                            docker push ${env.DOCKER_IMAGE}:latest
                        """
                    }
                }
            }
        }
        stage('Deploy to AKS'){
            steps{
                script{
                    def versionContent = readFile("${env.VERSION_FILE}")
                    def versionLine = versionContent.readLines().find { line ->
                        line.trim().startsWith('__version__')
                    }
                    def currentVersion = versionLine.split('=')[1].trim().replace('"', '').replace("'", '')
                    echo "Deploying version: ${currentVersion}"

                    withCredentials([
                            file(credentialsId: 'aks-kubeconfig', variable: 'KUBECONFIG_FILE')
                    ]) {
                            sh """
                                export KUBECONFIG=${KUBECONFIG_FILE}
                                kubectl get nodes
                                kubectl apply -f ${env.K8S_MANIFESTS_DIR}/
                                kubectl set image deployment/${env.APP_NAME} \
                                    ${env.APP_NAME}=${env.DOCKER_IMAGE}:${currentVersion} \
                                    -n ${env.K8S_NAMESPACE}
                                kubectl rollout status deployment/${env.APP_NAME} \
                                    -n ${env.K8S_NAMESPACE} \
                                    --timeout=300s
                                kubectl get pods -n ${env.K8S_NAMESPACE}
                            """

                            env.APP_PUBLIC_IP = sh(
                                returnStdout: true,
                                script: """
                                            export KUBECONFIG=${KUBECONFIG_FILE}
                                            kubectl get ingress -n ${env.K8S_NAMESPACE} \
                                                -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'
                                        """
                            ).trim()
                            echo "App Public IP: ${env.APP_PUBLIC_IP}"
                    }
                }
            }
        }
        stage('Commit Version Update'){
            steps{
                script{
                    def versionContent = readFile("${env.VERSION_FILE}")
                    def versionLine = versionContent.readLines().find { line ->
                        line.trim().startsWith('__version__')
                    }
                    def currentVersion = versionLine.split('=')[1].trim().replace('"', '').replace("'", '')
                    echo "Committing version: ${currentVersion}"

                    withCredentials([usernamePassword(
                        credentialsId: 'github-credentials',
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_PASS'
                    )]) {
                        sh """
                            echo "=== Committing version update ==="
                            git config --global user.email "jenkins@example.com"
                            git config --global user.name "jenkins CI"
                            git remote set-url origin https://${GIT_USER}:${GIT_PASS}@github.com/jfjc-zhoupan/sudoku-game-k8s.git

                            git add ${env.VERSION_FILE}
                            git commit -m "ci/cd: version bump to ${currentVersion} [skip ci]" || echo "No changes to commit"
                            git push origin HEAD:${env.BRANCH_NAME}
                            echo "Version update committed successfully to ${env.BRANCH_NAME}!"
                        """
                    }
                }
            }
        }
    }

    post{
        success {
            script {
                def versionContent = readFile("${env.VERSION_FILE}")
                def versionLine = versionContent.readLines().find { line ->
                    line.trim().startsWith('__version__')
                }
                def currentVersion = versionLine.split('=')[1].trim().replace('"', '').replace("'", '')
                env.NEW_VERSION = currentVersion
            }
            mail(
                subject: "App Deployment Success: ${env.APP_NAME} ${env.NEW_VERSION}",
                mimeType: 'text/plain',
                to: 'a572874046@163.com, raeezhao@gmail.com, a572874046@gmail.com',
                body: """
                    ============================================================
                    Application Deployment Complete!
                    ============================================================
                    Application: ${env.APP_NAME}
                    Version:     ${env.NEW_VERSION}
                    Image:       ${env.DOCKER_IMAGE}:${env.NEW_VERSION}
                    Namespace:   ${env.K8S_NAMESPACE}
                    Public URL:  http://${env.APP_PUBLIC_IP}
                    ============================================================
                    Test the Sudoku Game at the URL above!
                    ============================================================
                """
            )
            deleteDir()
        }
        failure{
            mail(
                subject: "App Deployment Failed: ${env.APP_NAME} - Build #${env.BUILD_NUMBER}",
                mimeType: 'text/plain',
                to: 'a572874046@163.com, a572874046@gmail.com',
                body: """
                    ============================================================
                    Application Pipeline Failed!
                    ============================================================
                    Application:    ${env.APP_NAME}
                    Original Ver:   ${env.ORIGINAL_VERSION}
                    Build Number:   ${env.BUILD_NUMBER}
                    Build URL:      ${env.BUILD_URL}
                    ============================================================
                """
            )
        }
    }
}