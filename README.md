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

## License - MIT

Copyright (C) 2019 Daniel Miranda

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
