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

        AZURE_SUBSCRIPTION_ID = '4b4511ba-165a-4df2-be28-75937cfe1031'
        AZURE_TENANT_ID       = '964f9745-bd07-4d1d-9a24-40f9bc141cc4'
        AZURE_APP_ID          = 'fcb81694-c5c2-4d1d-b349-665f8fb040d0'

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
        stage('Ensure App Routing') {
            steps {
                script {
                    withCredentials([
                            file(credentialsId: 'azure-terraform-pfx', variable: 'AZURE_PFX_FILE'),
                            string(credentialsId: 'azure-pfx-password', variable: 'AZURE_PFX_PASSWORD')
                        ]) {
                        sh """
                    set -e

                    # Copy pfx to a stable path (Jenkins temp dir may vanish between steps)
                    cp "\$AZURE_PFX_FILE" /tmp/azure-sp.pfx
                    chmod 600 /tmp/azure-sp.pfx

                    # Convert pfx to PEM (works with or without password)
                    if [ -n "\$AZURE_PFX_PASSWORD" ]; then
                        openssl pkcs12 -in /tmp/azure-sp.pfx -out /tmp/azure-sp.pem -nodes \
                            -passin pass:"\$AZURE_PFX_PASSWORD" 2>/dev/null || \
                        openssl pkcs12 -in /tmp/azure-sp.pfx -out /tmp/azure-sp.pem -nodes \
                            -passin pass:""
                    else
                        openssl pkcs12 -in /tmp/azure-sp.pfx -out /tmp/azure-sp.pem -nodes -passin pass:""
                    fi

                    # Login using the PEM certificate
                    az login --service-principal \
                        -u ${env.AZURE_APP_ID} \
                        -p /tmp/azure-sp.pem \
                        --tenant ${env.AZURE_TENANT_ID}

                    az account set -s ${env.AZURE_SUBSCRIPTION_ID}

                    # Check if App Routing is already enabled
                    ENABLED=\$(az aks show \
                        --resource-group ${env.AKS_RESOURCE_GROUP} \
                        --name ${env.AKS_CLUSTER_NAME} \
                        --query "addonProfiles.ingressApplicationRouting.enabled" \
                        -o tsv 2>/dev/null || echo "false")

                    if [ "\$ENABLED" = "true" ]; then
                        echo ">>> App Routing add-on already enabled."
                    else
                        echo ">>> Enabling App Routing add-on..."
                        az aks approuting enable \
                            --resource-group ${env.AKS_RESOURCE_GROUP} \
                            --name ${env.AKS_CLUSTER_NAME} \
                            --yes
                        echo ">>> App Routing enabled. Waiting for controller to provision LB..."
                        sleep 90
                    fi

                    # Clean up secrets
                    rm -f /tmp/azure-sp.pfx /tmp/azure-sp.pem
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
                def versionLine = versionContent.readLines().find { it.trim().startsWith('__version__') }
                def currentVersion = versionLine.split('=')[1].trim().replace('"', '').replace("'", '')

                // Re-fetch the ingress IP here, in case APP_PUBLIC_IP was lost due to the CPS bug
                def publicIp = env.APP_PUBLIC_IP
                if (!publicIp) {
                    withCredentials([file(credentialsId: 'aks-kubeconfig', variable: 'KUBECONFIG_FILE')]) {
                        publicIp = sh(
                            returnStdout: true,
                            script: """
                            export KUBECONFIG=${KUBECONFIG_FILE}
                            kubectl get ingress -n ${env.K8S_NAMESPACE} \
                                -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'
                        """
                        ).trim()
                    }
                }

                // Build the body with Groovy string interpolation (double quotes)
                def body = """
                ============================================================
                Application Deployment Complete!
                ============================================================
                Application: ${env.APP_NAME}
                Version:     ${currentVersion}
                Image:       ${env.DOCKER_IMAGE}:${currentVersion}
                Namespace:   ${env.K8S_NAMESPACE}
                Public URL:  http://${publicIp}
                ============================================================
                Test the Sudoku Game at the URL above!
                ============================================================
            """

                mail(
                    subject: "App Deployment Success: ${env.APP_NAME} ${currentVersion}",
                    mimeType: 'text/plain',
                    to: 'a572874046@163.com, raeezhao@gmail.com, a572874046@gmail.com',
                    body: body
                )
            }
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