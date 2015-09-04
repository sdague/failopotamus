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
import sys
import urllib
import webbrowser

from pyshorteners.shorteners import Shortener

PIPELINES = ('check', 'gate')
COLORS = (
    ('ff0000', 'b00000'),
    ('0000ff', '0000b0'),
    ('00ff00', '00b000'),
)


def parse_args():
    parser = argparse.ArgumentParser('failgraph')
    parser.add_argument('tests', metavar='testname', nargs='+')
    return parser.parse_args()


def graphite_base_url(since=200):
    ylabel = urllib.quote("Failure Rate in Percent")
    title = urllib.quote("Test failure rates over last %s hours" % since)
    return ("http://graphite.openstack.org/render/?from=-%dhours"
            "&height=500&until=now&width=800&bgcolor=ffffff"
            "&fgcolor=000000&yMax=100&yMin=0&vtitle=%s"
            "&title=%s"
    ) % (since, ylabel, title)


def failrate(job, queue, color, width=1):
    title = urllib.quote("%s (%s)" % (job, queue))
    return ("target=lineWidth(color("
            "alias("
            "movingAverage("
            "asPercent("
            "stats.zuul.pipeline.%(queue)s.job.%(job)s.FAILURE,"
            "sum(stats.zuul.pipeline.%(queue)s.job.%(job)s.{SUCCESS,FAILURE}))"
            ",%%27%(time)shours%%27),%%20%%27%(title)s%%27),"
            "%%27%(color)s%%27),"
            "%(width)s)" %
            {'job': job, 'queue': queue, 'time': 12,
             'color': color, 'title': title, 'width': width})


def get_targets(target, colors, avg=12):
    targets = []
    color = 0
    width = 1
    for pipeline in PIPELINES:
        targets.append(failrate(target, pipeline, colors[color], width))
        width += 1
        color += 1
    return targets


def main():
    args = parse_args()
    targetlist = ""
    colorpairs = 0
    for target in args.tests:
        targets = get_targets(target, COLORS[colorpairs])
        colorpairs += 1
        subtarglist = "&".join(targets)
        targetlist = "&".join([targetlist, subtarglist])
    url = "&".join((graphite_base_url(), targetlist))
    webbrowser.open(url)
    shortener = Shortener('TinyurlShortener')
    print "URL for sharing: %s" % shortener.short(url)


if __name__ == "__main__":
    sys.exit(main())
