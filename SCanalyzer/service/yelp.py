import requests
import pandas as pd
import geopandas as gpd
from pyproj import Transformer


def get_search_point(borders, epsg):
    max_x, min_x, max_y, min_y = borders
    # TODO: this might miss some locations, use diagonal
    radius = int(max(max_x - min_x, max_y - min_y) / 2)
    centroid_x = (max_x + min_x) / 2
    centroid_y = (max_y + min_y) / 2
    transformer = Transformer.from_crs(epsg, 4326)
    centroid_lat, centroid_lon = transformer.transform(centroid_x, centroid_y)
    return radius, centroid_lat, centroid_lon


def get_results(api_key, service, borders, epgs):
    limit = 50
    endpoint = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': 'bearer %s' % api_key}

    radius, centroid_lat, centroid_lon = get_search_point(borders, epgs)
    # print(radius, centroid_lat, centroid_lon)
    parameters = {
        'term': service,
        'limit': limit,
        'radius': min(radius, 40000),
        'latitude': centroid_lat,
        'longitude': centroid_lon}
    all_results = []
    response = requests.get(
        url=endpoint, params=parameters, headers=headers)
    result = response.json()
    # print(result.keys())
    all_results.extend(result['businesses'])

    found = result['total']
    searches = found // limit

    if searches != 0:
        try:
            for i in range(searches):
                offset = (i+1) * limit
                parameters['offset'] = offset
                response = requests.get(
                    url=endpoint, params=parameters, headers=headers)
                result = response.json()
                # print(len(all_results))
                all_results.extend(result['businesses'])
        except Exception as err:
            print(f'Unexpected {err=}')
    df = pd.DataFrame(
        columns=['id', 'service', 'name', 'latitude', 'longitude'])

    for i, row in enumerate(all_results):
        # print(i)
        df.loc[i, 'id'] = row['id']
        df.loc[i, 'service'] = service
        df.loc[i, 'name'] = row['name']
        df.loc[i, 'latitude'] = row['coordinates']['latitude']
        df.loc[i, 'longitude'] = row['coordinates']['longitude']

    return df
