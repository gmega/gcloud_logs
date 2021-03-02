#!/usr/bin/env python
#
# gcloud_logs.py: peek and tail Stackdriver logs for specific GKE instances
# usage: gcloud_logs.py [instance names] [options]
#        see gcloud_logs.py --help for a list of all options
#
# NOTE: This script will use your gcloud settings. You must, therefore, login
#       with gcloud and set a default project before launching it for the first
#       time.

import sys
import time
from argparse import ArgumentParser
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Callable, IO, Optional

import pytz
from colorama import Fore, Style
from dateutil import parser as date_parser
from google.cloud.logging_v2 import LogEntry, Client

#: When tailing, number of seconds to wait between successive attempts to pull new content.
POLL_INTERVAL = 1
#: How many log entries to retrieve per request.
PAGE_SIZE = 100


def main(args):
    formatter = api_format if args.api else line_format
    from_date = adjust_tz(args.from_date, args.utc)
    to_date = adjust_tz(args.to_date, args.utc)

    client = Client()
    with output_file(args) as outfile:
        tail(client, args.machine, from_date, formatter, outfile) if args.tail else \
            print_logs(client, args.machine, from_date, to_date, formatter, outfile)


def tail(client: Client, machines: List[str],
         from_date: datetime, formatter: Callable[[LogEntry], str], outfile: IO):
    low_watermark = from_date
    try:
        # When tailing, we loop trying to fetch log entries.
        while True:
            high_watermark = datetime.now().astimezone()
            # If a given query does not return any log entries, does not update the low_watermark as
            # otherwise we may lose stuff.
            if not print_logs(client, machines, low_watermark, high_watermark, formatter, outfile):
                low_watermark = high_watermark
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print(Fore.LIGHTRED_EX + 'CTRL+C pressed. Aborting.' + Fore.RESET, file=sys.stderr)


def print_logs(client: Client, machines: List[str],
               from_date: datetime, to_date: datetime,
               formatter: Callable[[LogEntry], str], outfile: IO) -> bool:
    empty = True
    for entry in client.list_entries(
            filter_=make_filter(machines, from_date, to_date),
            page_size=PAGE_SIZE
    ):
        print(formatter(entry), file=outfile)
        empty = False

    return empty


def api_format(response):
    return response.to_api_repr()


def line_format(response):
    json = response.to_api_repr()
    machine = json['resource']['labels']['instance_id']

    return Fore.LIGHTGREEN_EX + machine + Fore.LIGHTCYAN_EX + \
           f' [{json["timestamp"]}] ' + Style.BRIGHT + f"({json['severity']}): " + \
           Style.RESET_ALL + f"{json['textPayload']}"


def make_filter(machines, from_date, to_date=None):
    clauses = ['resource.type="gce_instance"']
    if machines:
        clause = ' OR '.join([f'resource.labels.instance_id="{instance_name}"' for instance_name in machines])
        clauses.append(f"({clause})")

    clauses.append(f'timestamp >= "{from_date.isoformat()}"')
    if to_date:
        clauses.append(f'timestamp <= "{to_date.isoformat()}"')

    return ' AND '.join(clauses)


def adjust_tz(ts: Optional[datetime], utc: bool) -> Optional[datetime]:
    # If the input already has a timezone baked in or the timezone is None, don't do anything.
    if ts is None or ts.tzinfo:
        return ts

    return ts.replace(tzinfo=pytz.UTC) if utc else ts.astimezone()


@contextmanager
def output_file(args):
    if args.to_file is None:
        yield sys.stdout
        return

    with open(args.to_file, 'w', encoding='utf-8') as outfile:
        yield outfile


def parse_opts():
    parser = ArgumentParser(description='Downloads and tails machine logs from Google Cloud')
    parser.add_argument('machine', metavar='MACHINE_NAME', nargs='*', help='machine names to pull logs from', type=str)
    parser.add_argument('--from-date', type=date_parser.parse,
                        help='starts pulling logs from this date and time. Defaults to 1 minute ago.',
                        default=datetime.now().astimezone() - timedelta(minutes=1))

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--to-date', help='streams logs until a specified date and time', type=date_parser.parse)
    group.add_argument('--tail', help='streams log to output, like in the "tail" command', action='store_true')

    parser.add_argument('--utc', help='treats --[from/to]-datetime as UTC timestamps instead '
                                      'of the local timezone', action='store_true')

    parser.add_argument('--to-file', help='outputs results to file instead of the standard output')
    parser.add_argument('--api', help='outputs Google API\'s JSON responses instead of log lines', action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    main(parse_opts())
