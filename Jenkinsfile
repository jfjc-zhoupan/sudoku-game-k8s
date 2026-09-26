pipeline {
    agent any
    environment {
        TF_DIR = 'terraform-infra'

        RESOURCE_GROUP = 'rg-sudoku-game'
        ACR_NAME = 'acrsudokugame'
        AKS_CLUSTER_NAME = 'aks-sudoku-game'

        TF_VAR_location = 'eastasia'
        TF_VAR_resource_group_name = 'rg-sudoku-game'
        TF_VAR_acr_name = 'acrsudokugame'
        TF_VAR_aks_cluster_name = 'aks-sudoku-game'

        ACR_LOGIN_SERVER = ''
    }

    stages {
        stage("Checkout"){
            steps{
                cleanWs()
                checkout scm
                script {
                    sh 'ls -la'
                    sh 'ls -la terraform/'
                }
            }
        }
        stage("Deploy Infrastructure"){
            steps{
                script{
                    withCredentials([
                            file(credentialsId: 'azure-terraform-pfx', variable: 'ARM_CLIENT_CERTIFICATE_PATH'),
                            string(credentialsId: 'azure-pfx-password', variable: 'ARM_CLIENT_CERTIFICATE_PASSWORD'),
                            string(credentialsId: 'azure-storage-key', variable: 'ARM_ACCESS_KEY')
                        ]) {
                        withEnv([
                                "ARM_CLIENT_ID=fcb81694-c5c2-4d1d-b349-665f8fb040d0",
                                "ARM_TENANT_ID=964f9745-bd07-4d1d-9a24-40f9bc141cc4",
                                "ARM_SUBSCRIPTION_ID=4b4511ba-165a-4df2-be28-75937cfe1031"
                            ]) {
                            sh """
                                cd ${env.TF_DIR}
                                terraform init
                                terraform plan
                                terraform apply -auto-approve
                            """
                            env.ACR_LOGIN_SERVER = sh(
                                returnStdout: true,
                                script: "cd ${env.TF_DIR} && terraform output -raw acr_login_server"
                            ).trim()
                        }
                    }
                }
            }
        }
    }

    post{
        success {
            mail(
                subject: "Infrastructure Deployment Success: Build #${env.BUILD_NUMBER}",
                mimeType: 'text/plain',
                to: 'a572874046@163.com, raeezhao@gmail.com, a572874046@gmail.com',
                body: """
                    ============================================================
                    Infrastructure Deployment Complete!
                    ============================================================
                    Branch:          ${env.BRANCH_NAME}
                    ACR Name:        ${env.ACR_NAME}
                    ACR Login Server:${env.ACR_LOGIN_SERVER}
                    AKS Cluster:     ${env.AKS_CLUSTER_NAME}
                    Resource Group:  ${env.RESOURCE_GROUP}
                    Build:           #${env.BUILD_NUMBER}
                    ============================================================
                    Next step: Run the 'application' pipeline to deploy the app.
                    ============================================================
                """
            )
        }
        failure{
            mail(
                subject: "Infrastructure Deployment Failed - Build #${env.BUILD_NUMBER}",
                mimeType: 'text/plain',
                to: 'a572874046@163.com, a572874046@gmail.com',
                body: """
                    ============================================================
                    Infrastructure Pipeline Failed!
                    ============================================================
                    Branch:       ${env.BRANCH_NAME}
                    Build Number: ${env.BUILD_NUMBER}
                    Build URL:    ${env.BUILD_URL}
                    ============================================================
                    Please check the Jenkins console for details.
                    ============================================================
                """
            )
        }
        always {
            cleanWs()
        }
    }
}