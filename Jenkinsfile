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
                cleanWs()
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
                    def version = parts[1].trim().replace('"', '').replace("'", '')
                    env.ORIGINAL_VERSION = String.valueOf(version)

                    def versionParts = env.ORIGINAL_VERSION.split('\\.')
                    def newPatch = (versionParts[2] as Integer) + 1
                    env.NEW_VERSION = "${versionParts[0]}.${versionParts[1]}.${newPatch}"

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
                    withCredentials([usernamePassword(
                                credentialsId: 'acr-credentials',
                                usernameVariable: 'ACR_USER',
                                passwordVariable: 'ACR_PASS'
                            )]) {
                        sh """
                            echo "${ACR_PASS}" | docker login ${env.ACR_SERVER} -u "${ACR_USER}" --password-stdin
                            cd ${env.APP_DIR}
                            docker build -t ${env.DOCKER_IMAGE}:${env.NEW_VERSION} .
                            docker tag ${env.DOCKER_IMAGE}:${env.NEW_VERSION} ${env.DOCKER_IMAGE}:latest

                            docker push ${env.DOCKER_IMAGE}:${env.NEW_VERSION}
                            docker push ${env.DOCKER_IMAGE}:latest
                        """
                    }
                }
            }
        }
        stage('Deploy to AKS'){
            steps{
                script{
                    withCredentials([
                        file(credentialsId: 'azure-terraform-pfx', variable: 'ARM_CLIENT_CERTIFICATE_PATH'),
                        string(credentialsId: 'azure-pfx-password', variable: 'ARM_CLIENT_CERTIFICATE_PASSWORD')
                    ]) {
                        withEnv([
                            "ARM_CLIENT_ID=fcb81694-c5c2-4d1d-b349-665f8fb040d0",
                            "ARM_TENANT_ID=964f9745-bd07-4d1d-9a24-40f9bc141cc4",
                            "ARM_SUBSCRIPTION_ID=4b4511ba-165a-4df2-be28-75937cfe1031"
                        ]) {
                            sh """
                                az aks get-credentials \
                                    --resource-group ${env.AKS_RESOURCE_GROUP} \
                                    --name ${env.AKS_CLUSTER_NAME} \
                                    --overwrite-existing

                                kubectl get nodes
                            """

                            sh """
                                kubectl apply -f k8s/aks/
                            """

                            sh """
                                echo "=== Updating deployment to ${env.DOCKER_IMAGE}:${env.NEW_VERSION} ==="
                                kubectl set image deployment/${env.APP_NAME} \
                                    ${env.APP_NAME}=${env.DOCKER_IMAGE}:${env.NEW_VERSION} \
                                    -n ${env.K8S_NAMESPACE}

                                echo "=== Waiting for rollout ==="
                                kubectl rollout status deployment/${env.APP_NAME} \
                                    -n ${env.K8S_NAMESPACE} \
                                    --timeout=300s

                                kubectl get pods -n ${env.K8S_NAMESPACE}
                            """

                            env.APP_PUBLIC_IP = sh(
                                returnStdout: true,
                                script: "kubectl get ingress -n ${env.K8S_NAMESPACE} -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'"
                            ).trim()
                            echo "App Public IP: ${env.APP_PUBLIC_IP}"
                        }
                    }
                }
            }
        }
        stage('Commit Version Update'){
            steps{
                script{
                    withCredentials([usernamePassword(
                        credentialsId: 'github-credentials',
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_PASS'
                    )]) {
                        sh """
                            echo "=== Committing version update ==="
                            git config --global user.email "jenkins@example.com"
                            git config --global user.name "jenkins CI"
                            git remote set-url origin https://${GIT_USER}:${GIT_PASS}@github.com/jfjc-zhoupan/sudoku-game.git

                            git add ${env.VERSION_FILE}
                            git commit -m "ci/cd: version bump to ${env.NEW_VERSION}" || echo "No changes to commit"
                            git push origin HEAD:${env.BRANCH_NAME}
                            echo "Version update committed successfully to ${env.BRANCH_NAME}!"
                        """
                    }
                }
            }
        }
        stage('Get Public IP'){
            steps{
                script{
                    def publicIp = sh(
                        returnStdout: true,
                        script: """kubectl get ingress -n ${env.K8S_NAMESPACE} -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'"""
                    ).trim()

                    if (!publicIp) {
                        error "Could not retrieve public IP from Ingress"
                    }

                    env.APP_PUBLIC_IP = publicIp
                    echo "App Public IP: ${env.APP_PUBLIC_IP}"
                }
            }
        }
    }

    post{
        success {
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
            script {
                try {
                    sh "git checkout ${env.VERSION_FILE} 2>/dev/null || echo 'Rollback skipped'"
                }
                catch (Exception e) {
                    echo "Rollback skipped: ${e.message}"
                }
            }
        }
        always {
            cleanWs()
        }
    }
}