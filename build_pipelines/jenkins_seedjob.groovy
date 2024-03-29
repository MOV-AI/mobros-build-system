def repoList = [:]
repoList = [
  1: [name:'amcl_movai', url: 'git@bitbucket.org:robosavvy/amcl_movai.git', branch: 'develop'],
  2: [name:'calibration_movai', url: 'git@bitbucket.org:robosavvy/calibration_movai.git', branch: 'master'],
  3: [name:'cart_detector', url: 'git@bitbucket.org:robosavvy/cart_detector.git', branch: 'master'],
  4: [name:'ioboard_driver_movai', url: 'git@bitbucket.org:robosavvy/ioboard_driver_movai.git', branch: 'develop'],
  5: [name:'lidar_slam_movai', url: 'git@bitbucket.org:robosavvy/lidar_slam_movai.git', branch: 'master'],
  6: [name:'movai_common', url: 'git@github.com:MOV-AI/movai_common.git', branch: 'master'],
  7: [name:'risk_prevention', url: 'git@bitbucket.org:robosavvy/risk_prevention.git', branch: 'master'],
  8: [name:'robot_safety_movai', url: 'git@bitbucket.org:robosavvy/robot_safety_movai.git', branch: 'master'],
  9: [name:'tb_common', url: 'git@bitbucket.org:robosavvy/tb_common.git', branch: 'master'],
  10: [name:'tb_configurations', url: 'git@bitbucket.org:robosavvy/tb_configurations.git', branch: 'master'],
  11: [name:'tb_factory', url: 'git@bitbucket.org:robosavvy/tb_factory.git', branch: 'master'],
  12: [name:'tb_ros', url: 'git@bitbucket.org:robosavvy/tb_ros.git', branch: 'master'],
  13: [name:'tb_software', url: 'git@bitbucket.org:robosavvy/tb_software.git', branch: 'master'],
  14: [name:'velodyne_movai', url: 'git@bitbucket.org:robosavvy/velodyne_movai.git', branch: 'master'],
  15: [name:'velodyne_movai', url: 'git@bitbucket.org:robosavvy/velodyne_movai.git', branch: 'master'],
  16: [name:'velodyne_movai', url: 'git@bitbucket.org:robosavvy/velodyne_movai.git', branch: 'main'],
  17: [name:'ompl', url: 'git@github.com:ompl/ompl.git', branch: '1.5.2' ]
]

// --- Create jobs list ---

def rosVersion = 'melodic' // 'noetic'
String dockerRegistry = 'registry.cloud.mov.ai'
String dockerCredentialsID = 'jenkins-registry-creds'
String nexusOSSURI = 'artifacts.cloud.mov.ai'
String nexusOSSRepositoryName = 'ppa-dev'
String nexusCredentialsID = 'nexus-credentials'
String awsSqsCredentialsID = 'mobros-sqs-user'

repoList.each { entry ->
    def repoName = entry.value.name
    def repoUrl = entry.value.url
    def repoBranch = entry.value.branch

    job(repoName) {
        scm {
            git {
                remote {
                    url(repoUrl)
                    credentials('bitbucket-ssh-credentials')
                    branch(repoBranch)
                }
                extensions {
                    wipeOutWorkspace()
                    submoduleOptions {
                        disable(false)
                        recursive(true)
                        parentCredentials(true)
                    }
                }
                branch(repoBranch)
            }
        }
        triggers {
            bitbucketPush()
        }
        wrappers {
            colorizeOutput()
            timestamps()
            credentialsBinding {
                usernamePassword('NEXUS_CREDENTIALS_USR', 'NEXUS_CREDENTIALS_PSW', nexusCredentialsID)
                usernamePassword('DOCKER_REGISTRY_CREDS_USR', 'DOCKER_REGISTRY_CREDS_PSW', dockerCredentialsID)
                usernamePassword('AWS_SQS_CREDS_USR', 'AWS_SQS_CREDS_PSW', awsSqsCredentialsID)
            }
        }
        steps {
            environmentVariables {
                envs(
                    ROS_DISTRO: "${rosVersion}",
                    DOCKER_REGISTRY: "${dockerRegistry}" ,
                    NEXUS_REGISTRY: "${nexusOSSURI}",
                    NEXUS_PPA: "${nexusOSSRepositoryName}",
                    ROS_BUILDTOOLS_DOCKER_IMAGE: "${dockerRegistry}/devops/ros-buildtools:${rosVersion}",
                    JOB_NAME: "${repoName}",
                    IN_CONTAINER_MOUNT_POINT: '/opt/mov.ai/user/cache/ros/src',
                    IN_CONTAINER_ROS_PACKAGES: '/tmp/packages'
                )
            }
            shell('''#!/bin/bash
set -e

DOCKER_MOUNT_DIR="/opt/jenkins/data/workspace/movai_debs_$ROS_DISTRO/$JOB_NAME"

docker_args="""-t -d -u movai --entrypoint=  \
-v $DOCKER_MOUNT_DIR:$IN_CONTAINER_MOUNT_POINT \
-v /opt/jenkins/data/.gnupg:/opt/mov.ai/.gnupg \
-e IN_CONTAINER_MOUNT_POINT=${IN_CONTAINER_MOUNT_POINT} \
-e IN_CONTAINER_ROS_PACKAGES=${IN_CONTAINER_ROS_PACKAGES} \
-e PYLOGLEVEL=DEBUG \
-e AWS_DEFAULT_REGION="eu-west-1" \
-e AWS_ACCESS_KEY_ID=$AWS_SQS_CREDS_USR \
-e AWS_SECRET_ACCESS_KEY=$AWS_SQS_CREDS_PSW
"""

docker login ${DOCKER_REGISTRY} --username ${DOCKER_REGISTRY_CREDS_USR} --password ${DOCKER_REGISTRY_CREDS_PSW}

docker pull $ROS_BUILDTOOLS_DOCKER_IMAGE

echo ">>> Running docker $ROS_BUILDTOOLS_DOCKER_IMAGE with args $docker_args"
container_id=$(docker run $docker_args $ROS_BUILDTOOLS_DOCKER_IMAGE cat)

echo ">>> Exec in $container_id"

docker exec -u movai --tty "$container_id" bash -c """
    python3 -m pip install mobros==1.0.0 --ignore-installed
    echo $PATH
    export PATH=/opt/mov.ai/.local/bin:$PATH
    mobros build
    mobros pack --workspace=\${IN_CONTAINER_MOUNT_POINT}
    mobros publish
    """ || true

echo ">>> Exiting of $container_id"

echo ">>> Deleting container: $container_id"
docker rm -f $container_id

''')
        }
        publishers {
            wsCleanup ()
            postBuildScript {
                markBuildUnstable(true)
                buildSteps {
                    postBuildStep {
                        results(['SUCCESS'])
                        stopOnFailure(true)
                        buildSteps {
                            shell {
                                command ('''#!/bin/bash
              for debfiles in $(find ./ -name "*.deb"); do
                echo Pushing $debfiles
                curl --silent --show-error --fail -u "${NEXUS_CREDENTIALS_USR}:${NEXUS_CREDENTIALS_PSW}" "https://$NEXUS_REGISTRY/service/rest/v1/components?repository=$NEXUS_PPA" \
                -H "Content-Type: multipart/form-data" \
                -F apt.asset=@$debfiles
              done
              ''')
                            }
                            archiveArtifacts('*.deb')
                        }
                    }
                }
            }
        }
    }
    queue(repoName)
}

//String nexusOSSVersion = 'nexus3'
//nexusArtifactUploader {
//      nexusVersion(nexusOSSVersion)
//      protocol(HTTP)
//      nexusUrl(nexusOSSURI)
//version('${POM_VERSION}')
//      repository(nexusOSSRepositoryName)
//      credentialsId(nexusCredentialsID)
//      artifact {
//          artifactId("${repoName}")
//          type('apt')
//          classifier('')
//          file('*/*.deb')
//      }
//     }
//  }
