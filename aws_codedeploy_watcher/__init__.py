import logging
import re
import sys
import time
from argparse import ArgumentParser

import boto3.session

from .deploy import DeploymentWatcher
from .logs import find_log_groups


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger('aws-codedeploy-watcher').setLevel(logging.DEBUG)

    argp = ArgumentParser(description='Observe Codedeploy deployments')
    argp.add_argument(
        '--deployment-id', required=True,
        help='ID of the Codedeploy deployment to watch')
    argp.add_argument(
        '--log-group-prefix',
        help='Prefix of the Cloudwatch log group names to follow')
    argp.add_argument(
        '--log-group-pattern', type=re.compile,
        help='Regular expression for matching the Cloudwatch log group names '
             'to follow. Use it only for selections that can\'t be done with '
             'just the prefix, as this will require loading all the groups and'
             'filtering locally.')
    argp.add_argument(
        '--start-timeout', type=float, metavar='SECONDS', default=60,
        help='How long to wait for a Pending deployment to start')
    argp.add_argument(
        '--stop-on-interrupt', action='store_true',
        help='Cancel deployment if the program is inter')

    args = argp.parse_args()

    session = boto3.session.Session()
    log_group_names = list(find_log_groups(session, args.log_group_prefix,
                                           args.log_group_pattern))

    logger.info('Found log groups: {}'.format(', '.join(log_group_names)))

    d_id = args.deployment_id
    watcher = DeploymentWatcher(
        session, d_id, log_group_names, out_file=sys.stderr)

    watcher.wait_started(args.start_timeout)
    try:
        while not watcher.is_finished():
            watcher.follow()
            time.sleep(1)
    except Exception:
        if args.stop_on_interrupt:
            watcher.stop_deployment()

        raise

    watcher.display()

    if watcher.failed():
        logger.error(
            'Deployment {} finished with failed status: {}'.format(
                d_id, watcher.status))
        sys.exit(1)

    logger.info('Deployment {} finished successfully'.format(d_id))
