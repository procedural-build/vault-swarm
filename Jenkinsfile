pipeline {
  agent any

  environment {
    WORKSPACE_DIR = """${sh(
        returnStdout: true,
        script: 'echo -n "${WORKSPACE##*/}"'
    )}"""
    HOST_SRC_PATH = """${sh(
        returnStdout: true,
        script: 'echo -n "$HOST_WORKSPACE_PATH${WORKSPACE##*/}/"'
    )}"""
    DOCKER_VERSION = """${sh(
        script: 'echo -n "$(date +%Y.%m.%d)-\$(git rev-parse --short HEAD)"',
        returnStdout: true
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
        script {
            env.BUILD_DATE = new Date().format('YYYY-MM-dd HH:mm:ss', TimeZone.getTimeZone('UTC'))
        }
        sh '''docker build \
        --target production \
        --build-arg DOCKER_TAG=$DOCKER_VERSION \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg GIT_COMMIT=$GIT_COMMIT \
        --build-arg BRANCH=$BRANCH_NAME \
        -t vault-swarm:$BRANCH_NAME .'''
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
    }
  }

}
