import logging
import re
import sys

import pendulum
import botocore.exceptions


logger = logging.getLogger(__name__)


def find_log_groups(session, prefix, pattern):
    compiled_pat = re.compile(pattern)

    client = session.client('logs')
    describe_log_groups = client.get_paginator('describe_log_groups').paginate
    for groups in describe_log_groups(logGroupNamePrefix=prefix):
        for group in groups['logGroups']:
            group_name = group['logGroupName']
            assert group_name.startswith(prefix)

            group_suffix = group_name[len(prefix):]
            if compiled_pat.search(group_suffix):
                yield group_name


class LogWatcher(object):
    def __init__(self, session, out_file=sys.stderr):
        self._client = session.client('logs')
        self._log_streams = {}
        self._group_timestamps = {}
        self._out_file = out_file

        self._filter_log_events = \
            self._client.get_paginator('filter_log_events').paginate

        self._start_ts = None
        self._end_ts = None

    def add_log_stream(self, group_name, stream_name, start_time=None):
        stream_names = self._log_streams.setdefault(group_name, set())
        stream_names.add(stream_name)

        if start_time:
            start_time = pendulum.instance(start_time)
            self._group_timestamps[group_name] = \
                int(start_time.timestamp * 1000)

    def remove_log_stream(self, group_name, stream_name):
        stream_names = self._log_streams.setdefault(group_name, set())
        stream_names.discard(stream_name)

    def set_time_range(self, start=None, end=None):
        if start:
            start = pendulum.instance(start)
            self._start_ts = int(start.float_timestamp * 1000)
        else:
            self._start_ts = None

        if end:
            end = pendulum.instance(end)
            self._end_ts = int(end.float_timestamp * 1000)
        else:
            self._end_ts = None

    def _event_time(self, event):
        event_ts = event.get('timestamp') or event['ingestionTime']
        return pendulum.from_timestamp(event_ts / 1000)

    def follow(self):
        for group_name, stream_names in self._log_streams.items():
            if not stream_names:
                continue

            last_ts = self._group_timestamps.get(group_name, self._start_ts)
            end_ts = self._end_ts

            try:
                logger.debug('Calling filter_log_events: {}'.format(dict(
                    logGroupName=group_name,
                    logStreamNames=list(stream_names),
                    startTime=last_ts,
                    endTime=end_ts)))

                event_batches = self._filter_log_events(
                    logGroupName=group_name,
                    logStreamNames=list(stream_names),
                    startTime=last_ts,
                    endTime=end_ts)

                for batch in event_batches:
                    for event in batch['events']:
                        yield self._event_time(event), group_name, event
                        last_ts = max(last_ts, event['ingestionTime'])
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise

            self._group_timestamps[group_name] = last_ts
