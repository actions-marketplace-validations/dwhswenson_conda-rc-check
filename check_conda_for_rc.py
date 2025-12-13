#!/usr/bin/env python

import argparse
import datetime
import dateutil.parser
import packaging.version
import requests

def fetch_files(package):
    url = f"https://api.anaconda.org/package/{package}/files"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def parse_file_entry(entry):
    version = packaging.version.Version(entry["version"])
    uploaded_at = dateutil.parser.parse(entry["upload_time"])
    labels = entry.get("labels") or []
    return version, uploaded_at, labels

def get_releases_since_days_ago(package, oldest_allowed):
    releases = []
    for entry in fetch_files(package):
        version, uploaded_at, labels = parse_file_entry(entry)
        if uploaded_at >= oldest_allowed:
            releases.append((version, uploaded_at, labels))
    return releases

def find_rcs(releases, tags):
    filtered = releases
    if tags:
        filtered = [r for r in filtered if any(label in tags for label in r[2])]

    versions = set(r[0] for r in filtered)
    rcs = [v for v in versions if v.pre and 'rc' in v.pre]
    return rcs

def main(package, n_days=7, allowed_tags=None):
    oldest_allowed = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=n_days)
    releases = get_releases_since_days_ago(package, oldest_allowed)
    rcs = find_rcs(releases, allowed_tags)
    #print(rcs)
    return bool(rcs)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('channel', type=str)
    parser.add_argument('package', type=str)
    parser.add_argument('n_days', type=int)
    parser.add_argument('tags', type=str)
    opts = parser.parse_args()
    package = f"{opts.channel}/{opts.package}"
    tags = opts.tags.split()
    return package, opts.n_days, tags


if __name__ == "__main__":
    package, n_days, tags = parse_args()
    result = main(package, n_days, tags)
    print(f"::set-output name=hasrc::{result}")
