#!/usr/bin/env python

# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import json
import sys
import urllib
import webbrowser

import requests

from pyshorteners.shorteners import Shortener

PIPELINES = ('check', 'gate')
COLORS = (
    ('ff0000', 'b00000'),
    ('0000ff', '0000b0'),
    ('00ff00', '00b000'),
)


def parse_args():
    parser = argparse.ArgumentParser(
        'failgraph',
        description="""
    Generate nice failure graphs from graphite based on job name.
    """)
    parser.add_argument('-d', '--duration',
                        type=int, default=200,
                        help="Graph over ``duration`` hours (default 200)"
    )
    parser.add_argument('-s', '--smoothing',
                       type=int, default=12,
                       help="Rolling average hours (defaults to 12)")
    parser.add_argument('tests', metavar='testname', nargs='+')
    return parser.parse_args()


def graphite_base_url(since, avg):
    ylabel = urllib.quote("Failure Rate in Percent")
    title = urllib.quote("Test failure rates over last %s hours "
                         "(%s hour rolling average)" % (since, avg))
    return ("http://graphite.openstack.org/render/?from=-%dhours"
            "&height=500&until=now&width=800&bgcolor=ffffff"
            "&fgcolor=000000&yMax=100&yMin=0&vtitle=%s"
            "&title=%s&drawNullAsZero=true"
    ) % (since, ylabel, title)


def failrate(job, queue, color, width=1, avg=12):
    title = urllib.quote("%s (%s)" % (job, queue))
    return ("target=lineWidth(color("
            "alias("
            "movingAverage("
            "asPercent("
            "transformNull("
            "stats_counts.zuul.pipeline.%(queue)s.job.%(job)s.FAILURE),"
            "transformNull(sum(stats_counts.zuul.pipeline.%(queue)s."
            "job.%(job)s.{SUCCESS,FAILURE})))"
            ",%%27%(time)shours%%27),%%20%%27%(title)s%%27),"
            "%%27%(color)s%%27),"
            "%(width)s)" %
            {'job': job, 'queue': queue, 'time': avg,
             'color': color, 'title': title, 'width': width})


def target_in_pipeline(target, pipeline):
    json_data = ("http://graphite.openstack.org/render?target="
               "stats.zuul.pipeline.%s.job.%s.*&format=json" %
               (pipeline, target))
    resp = requests.get(json_data)
    data = json.loads(resp.content)
    # if the data is blank, this doesn't exist on the graphite server at all
    return data != []


def get_targets(target, colors, avg=12):
    targets = []
    color = 0
    width = 1
    for pipeline in PIPELINES:
        if target_in_pipeline(target, pipeline):
            targets.append(
                failrate(target, pipeline, colors[color], width, avg))
            width += 1
            color += 1
    return targets


def get_graphite_url(tests, smoothing, duration):
    targetlist = ""
    colorpairs = 0
    for target in tests:
        targets = get_targets(target, COLORS[colorpairs % len(COLORS)],
                              avg=smoothing)
        colorpairs += 1
        subtarglist = "&".join(targets)
        targetlist = "&".join([targetlist, subtarglist])
    url = "&".join((
        graphite_base_url(duration, smoothing), targetlist))
    return url


def main():
    args = parse_args()
    url = get_graphite_url(args.tests, args.smoothing, args.duration)
    webbrowser.open(url)
    shortener = Shortener('TinyurlShortener')
    print "URL for sharing: %s" % shortener.short(url)


if __name__ == "__main__":
    sys.exit(main())
