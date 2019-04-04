from __future__ import print_function

import sys

import pendulum

from .logs import LogWatcher


class DeploymentWatcher(object):
    def __init__(self, session, deployment_id, log_group_names=None,
                 out_file=sys.stderr):
        self.deployment_id = deployment_id
        self.status = None
        self.log_group_names = log_group_names or []

        self._client = session.client('codedeploy')
        self._list_deployment_targets = \
            self._client.get_paginator('list_deployment_targets').paginate
        self._out_file = out_file

        self._target_ids = None
        self._target_lifecycle_events = {}
        self._targets = None
        self._log_watcher = LogWatcher(session, out_file=out_file)
        self._last_update_time = None
        self._complete_time = None

    def is_finished(self):
        return self.status in ('Succeeded', 'Failed')

    def is_target_active(self, target):
        return target['status'] == 'InProgress'

    def is_target_finished(self, target):
        return target['status'] in ('Succeeded', 'Failed', 'Skipped', 'Ready')

    def get_target_ids(self):
        if self._target_ids is None:
            def _get_target_ids():
                targets = self._list_deployment_targets(
                    deploymentId=self.deployment_id)
                for response in targets:
                    for target_id in response['targetIds']:
                        yield target_id

            self._target_ids = list(_get_target_ids())

        return self._target_ids

    def get_targets(self, types):
        target_ids = self.get_target_ids()

        response = self._client.batch_get_deployment_targets(
            deploymentId=self.deployment_id, targetIds=target_ids)

        for target in response['deploymentTargets']:
            target_type = target['deploymentTargetType']
            if target_type not in types:
                continue

            if target_type == 'InstanceTarget':
                target_info = target['instanceTarget']
            elif target_type == 'ECSTarget':
                target_info = target['ecsTarget']
            elif target_type == 'LambdaTarget':
                target_info = target['lambdaTarget']
            else:
                continue

            yield target_info['targetId'], target_info

    def enable_log_target(self, target_id, start_time=None):
        for group_name in self.log_group_names:
            self._log_watcher.add_log_stream(group_name, target_id,
                                             start_time=start_time)

    def disable_log_target(self, target_id):
        for group_name in self.log_group_names:
            self._log_watcher.remove_log_stream(group_name, target_id)

    def _event_time(self, event):
        start_time = event.get('startTime')
        end_time = event.get('endTime')

        if end_time:
            return pendulum.instance(end_time)
        elif start_time:
            return pendulum.instance(start_time)
        elif self._complete_time:
            return self._complete_time
        else:
            return pendulum.now()

    def get_updated_lifecycle_events(self, target_id, events):
        target_events = self._target_lifecycle_events.setdefault(target_id, {})

        for event in events:
            event_name = event['lifecycleEventName']
            prev_event = target_events.get(event_name)
            if not prev_event or event != prev_event:
                # Accumulate entries for the events with the respective
                # times so they can be printed in order
                event_entry = (self._event_time(event), target_id, event)
                yield event_entry

                target_events[event_name] = event

    def update(self):
        response = \
            self._client.get_deployment(deploymentId=self.deployment_id)

        self._deploy_info = response['deploymentInfo']
        self.status = self._deploy_info['status']

        if not self._complete_time and self.is_finished():
            self._complete_time = \
                pendulum.instance(self._deploy_info['completeTime'])
        self._targets = dict(
            self.get_targets(types=('InstanceTarget', 'ECSTarget')))

    def display(self):
        assert self.is_finished()

        create_time = self._deploy_info.get('createTime')
        start_time = self._deploy_info.get('startTime')
        self._log_watcher.set_time_range(
            start=start_time or create_time,
            end=self._complete_time)

        for target_id in self._targets.keys():
            self.enable_log_target(target_id)

        self.print_log_messages()

    def follow(self):
        self.update()

        new_update_time = self._last_update_time
        fresh_events = []

        for target_id, target in self._targets.items():
            updated_at = target['lastUpdatedAt']
            if updated_at <= self._last_update_time:
                continue

            new_update_time = max(new_update_time, updated_at)

            events = self.get_updated_lifecycle_events(
                target_id, target['lifecycleEvents'])
            fresh_events.extend(events)

            if not self.is_finished():
                if self.is_target_active(target):
                    self.enable_log_target(target_id, self._last_update_time)
                elif self.is_target_finished(target):
                    self.disable_log_target(target_id)

        self._last_update_time = new_update_time

        self.print_lifecycle_events(fresh_events)
        self.print_log_messages()

    def print_lifecycle_events(self, events):
        for event_time, target_id, event in sorted(events):
            self.print_lifecycle_event(event_time, target_id, event)

    def print_lifecycle_event(self, event_time, target_id, event):
        message = event.get('diagnostics', {}).get('message', '')
        if message == event['status']:
            message = ''
        if message:
            message = '- ' + message

        msg = '{} ({}): [{}] {}: {} {}'.format(
            self.deployment_id, target_id, event_time.to_datetime_string(),
            event['lifecycleEventName'], event['status'], message)
        print(msg, file=self._out_file)

    def print_log_messages(self):
        events = sorted(self._log_watcher.follow())
        for event_time, group_name, event in events:
            target_id = event['logStreamName']
            msg = '{} ({}): [{}] {}'.format(
                self.deployment_id, target_id, event_time.to_datetime_string(),
                event['message'])
            print(msg, file=self._out_file)
