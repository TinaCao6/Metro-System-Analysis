import pandas as pd
from datetime import datetime
from pyproj import CRS, Transformer
import os
import random
import math

# for quick debugging
debug = True


def dprint(cmd):
    if debug:
        print(cmd)


def fmin(minutes):
    return f"{minutes // 60}:{minutes % 60}:00"


def tomin(time_string):
    time_li = time_string.split(":")
    h = int(time_li[0])
    m = int(time_li[1])
    return h * 60 + m


def fsec(seconds):
    h = seconds // 3600
    m = (seconds - 3600 * h) // 60
    s = seconds - 3600 * h - 60 * m
    return f"{h}:{m}:{s}"


def tosec(time_string):
    time_li = time_string.split(":")
    h = int(time_li[0])
    m = int(time_li[1])
    s = int(time_li[2])
    return h * 3600 + m * 60 + s


def gen_start_time(interval, elapse_time):
    start_times = []
    curr = 0
    interval = tomin(interval)
    elapse_time = tomin(elapse_time)
    min_total = 24 * 60 - elapse_time
    while curr <= min_total:
        start_times.append(fmin(curr))
        curr += interval

    return start_times


def gen_locations(data_path, num):
    mmt_gtfs_path = os.path.join(data_path, "mmt_gtfs")
    stops_df = pd.read_csv(os.path.join(
        mmt_gtfs_path, "stops.csv"), sep=",")
    locations = []

    lat_min = stops_df.stop_lat.min()
    lat_max = stops_df.stop_lat.max()
    lon_min = stops_df.stop_lon.min()
    lon_max = stops_df.stop_lon.max()

    for i in range(num):
        lat = random.random() * (lat_max - lat_min) + lat_min
        lon = random.random() * (lon_max - lon_min) + lon_min
        locations.append((lat, lon))

    return locations


# for parsing perf logs
def parse_log_line(line):
    line = line.strip()
    tokens = line.split(" - ")
    timestamp = datetime.strptime(tokens[0], "%Y-%m-%d %H:%M:%S,%f")
    level = tokens[1]
    msg = tokens[2]
    return timestamp, level, msg


def to_millisecs(timedelta):
    return timedelta.total_seconds() * 1000


def get_perf(log_path):

    perf = pd.DataFrame()
    graph_search = projections = uninioning = None
    graph_search_ts = projections_ts = uninioning_ts = None
    i = 0

    with open(log_path) as f:
        for line in f:
            timestamp, level, msg = parse_log_line(line)

            if msg == "Start searching graph":
                # print(1)
                graph_search_ts = timestamp
            elif msg == "start generating gdf":
                # print(2)
                projections_ts = timestamp
                graph_search = projections_ts - graph_search_ts
            elif msg == "start calculating union/difference":
                # print(3)
                uninioning_ts = timestamp
                projections = uninioning_ts - projections_ts
            elif msg == "finish calculating area":
                # print(4)
                uninioning = timestamp - uninioning_ts
                # flush all previous results
                perf.loc[i, "graph_search"] = to_millisecs(graph_search)
                perf.loc[i, "projections"] = to_millisecs(projections)
                perf.loc[i, "uninioning"] = to_millisecs(uninioning)
                graph_search = projections = uninioning = None
                graph_search_ts = projections_ts = uninioning_ts = None
                i += 1

    return perf


# for transforming CRS
# https://epsg.io/3174
_transformer = None

def getZones(lat, lon):
    if lat >= 72.0 and lat < 84.0:
        if lon >= 0.0 and lon < 9.0:
            return 31
        if lon >= 9.0 and lon < 21.0:
            return 33
        if lon >= 21.0 and lon < 33.0:
            return 35
        if lon >= 33.0 and lon < 42.0:
            return 37
    if lat >= 56 and lat < 64.0 and lon >= 3 and lon <= 12:
        return 32
    return math.floor((lon + 180) / 6) + 1


def findEPSG(lat, lon) :
    zone = getZones(lat, lon)
    #zone = (math.floor((longitude + 180) / 6) ) + 1  # without special zones for Svalbard and Norway         
    epsg_code = 32600
    epsg_code += int(zone)
    if (lat< 0): # South
        epsg_code += 100    
    return epsg_code


def transform(lat, lon):
    global _transformer

    epsg=findEPSG(lat,lon)
    if _transformer is None:
        _transformer = Transformer.from_crs(4326, epsg)
    return _transformer.transform(lat, lon)

# for serializing grid to bitmap string


def serialize_grid():
    pass


def deserialize_grid():
    pass
