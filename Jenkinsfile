pipeline {
  agent any

  environment {
    SLACK = credentials('slack')
    WORKSPACE_DIR = """${sh(
            returnStdout: true,
            script: 'echo -n "${WORKSPACE##*/}"'
        )}"""
    HOST_SRC_PATH = """${sh(
            returnStdout: true,
            script: 'echo -n "$HOST_WORKSPACE_PATH${WORKSPACE##*/}/"'
        )}"""
  }

  stages {
    stage('Check Jenkins/Docker') {
      steps {
        sh 'docker version'
      }
    }

    stage('Docker Build') {
      steps {
        env.DOCKER_VERSION = "$(date +%Y.%m.%d)-$(git rev-parse --short HEAD)"
        sh 'echo "$(date +%Y.%m.%d)-$(git rev-parse --short HEAD)" > VERSION'
        sh 'docker build --target production -t vault-swarm:$BRANCH_NAME .'
      }
    }

    stage('Test') {
      steps {
        echo "HERE SHOULD BE TESTS"
        //sh 'chmod +x docker/runTest.sh'
        //sh 'docker/runTest.sh'
      }
      post {
        always {
          echo "COLLECT TEST RESULTS"
          //junit "test_data/test-results.xml"
        }
      }
    }
    stage('Deployment') {
      when {
        anyOf {
          branch 'master'
          branch 'stage'
        }
      }

      steps {
        script {
          if (env.BRANCH_NAME == 'master') {
            env.DOCKER_TAG = 'stable'
          } else {
            env.DOCKER_TAG = 'latest'
          }

          sh('\$(aws ecr get-login --region eu-west-2 --no-include-email)')
          sh('docker tag "vault-swarm:$BRANCH_NAME" "598950368936.dkr.ecr.eu-west-2.amazonaws.com/vault-swarm:$DOCKER_TAG"')
          sh('docker tag "vault-swarm:$BRANCH_NAME" "598950368936.dkr.ecr.eu-west-2.amazonaws.com/vault-swarm:$DOCKER_VERSION"')
          docker.withRegistry("https://598950368936.dkr.ecr.eu-west-2.amazonaws.com"){docker.image("598950368936.dkr.ecr.eu-west-2.amazonaws.com/vault-swarm:$DOCKER_TAG").push("$DOCKER_TAG")}
          docker.withRegistry("https://598950368936.dkr.ecr.eu-west-2.amazonaws.com"){docker.image("598950368936.dkr.ecr.eu-west-2.amazonaws.com/vault-swarm:$DOCKER_TAG").push("$DOCKER_VERSION")}
        }
      }
    }
  }
  post {

    always {
      cleanWs()

      script {
        sh 'docker container prune -f'
        sh 'docker volume prune -f'
      }
    }

    success {
      slackSend(
         message: "SUCCESS\nJob: ${env.JOB_NAME} \nBuild ${env.BUILD_DISPLAY_NAME} \n URL: ${env.RUN_DISPLAY_URL} \n Latest Stage Coverage Report: https://docs.procedural.build/track/coverage/",
         color: "good",
         token: "${SLACK}",
         baseUrl: 'https://traecker.slack.com/services/hooks/jenkins-ci/',
         channel: '#jenkins-ci'
      )
    }

    failure {
       slackSend(
         message: "FAILED\nJob: ${env.JOB_NAME} \nBuild ${env.BUILD_DISPLAY_NAME} \n URL: ${env.RUN_DISPLAY_URL}",
         color: "#fc070b",
         token: "${SLACK}",
         baseUrl: 'https://traecker.slack.com/services/hooks/jenkins-ci/',
         channel: '#jenkins-ci'
       )
    }
  }

}
