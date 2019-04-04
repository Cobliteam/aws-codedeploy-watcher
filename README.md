# AWS Codedeploy watcher

Observe AWS Codedeploy deployments live

## Installation

    pip install aws-codedeploy-watcher


## Usage

    usage: aws-codedeploy-watcher [-h] --deployment-id DEPLOYMENT_ID
                                  [--log-group-prefix LOG_GROUP_PREFIX]
                                  [--log-group-pattern LOG_GROUP_PATTERN]
    
    Observe Codedeploy deployments
    
    optional arguments:
      -h, --help            show this help message and exit
      --deployment-id DEPLOYMENT_ID
                            ID of the Codedeploy deployment to watch
      --log-group-prefix LOG_GROUP_PREFIX
                            Prefix of the Cloudwatch log group names to follow
      --log-group-pattern LOG_GROUP_PATTERN
                            Regular expression for matching the Cloudwatch log
                            group names to follow. Use it only for selections that
                            can't be done with just the prefix, as this will
                            require loading all the groups andfiltering locally.

