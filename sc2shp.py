"""
Simple script to parse GPS data from Storage Connect into a GeoDataFrame and export to OGC GeoPackage (Shapefiles can't handle datetime fields)
@author jonnyhuck

Data Source:
    https://storageconnect.its.manchester.ac.uk/Data/Export/579ad18d-4732-402d-822f-38da12e9edc5

Example Usage:
    python sc2shp.py -i "./Export2022-04-19T16-23-09.json" -o "./gps_traces.gpkg"
"""

from json import load as load_json
from shapely.geometry import Point
from geopandas import GeoDataFrame
from argparse import ArgumentParser
from fiona.errors import DriverIOError
from pandas import DataFrame, concat, to_datetime, merge

def parse_data(in_path, out_path="", export=True, report=True, debug=False):
    """
    Parse json data and export to Shapefile

    @param in_path:     (str) file path for the *.json file to be parsed
    @param out_path:    (str) file path for the output *.gpkg file (only used if `export=True`) 
    @param export:      (boolean) indicating whether a *.gpkg file should be exported
    @param report:      (boolean) indicating whether to report the number of points per user
    @param debug:       (boolean) indicating whether to output data packets that failed to import to the console
    """
    # ensure input is a JSON file
    if in_path[-5:] != ".json":
        print("ERROR: Input file must be *.json file")
        exit(1)
    
    # ensure output is shapefile
    if export:
        if out_path[-5:] != ".gpkg":
            print("ERROR: Output file path must be *.gpkg if --export=True")
            exit(1)

    # load and parse json dataset
    try:
        with open(in_path) as json_file:
            data = load_json(json_file)
            print(f"retrieved {len(data['packets'])} packets...")
    except FileNotFoundError:
        print("Input file not found")
        exit(1)

    # loop therough each data packet
    dfs = []
    for d in data['packets']:

        # construct dataframe and load into list
        try:
            dfs.append(DataFrame({
                'user_id':          [d['user_id']]*len(d['longitude']),
                'longitude':        [float(n.replace(",",".")) for n in d['longitude']],
                'latitude':         [float(n.replace(",",".")) for n in d['latitude']],
                'timestamp':        d['timestamp'],
                'accuracy':         [int(n) for n in d['accuracy']],
                'device_details':   [d['device_details']]*len(d['longitude']),
            }))
        except (KeyError, ValueError) as e:
            if debug:
                print(e)
                print(d['user_id'])
                print(d['longitude'])
                print(d['latitude'])
                print(d['timestamp'])
                print(d['accuracy'])
                print(d['device_details'])
                print()
            continue

    # concat all DataFrames into a single one
    df = concat(dfs)
    print(f"\t...comprising {len(df.index)} records")

    # parse date and time
    df['timestamp'] = to_datetime(df['timestamp'], infer_datetime_format=True)

    # convert to geodataframe
    gdf = GeoDataFrame(
        df.drop(['longitude', 'latitude'], axis=1),
        crs='+proj=longlat +datum=WGS84 +no_defs',
        geometry=[Point(ll) for ll in zip(df.longitude, df.latitude)])
    del df

    # report user data (lazily via table join...)
    if report:
        print()
        print(merge(\
            left=gdf['timestamp'].groupby(gdf['user_id']).agg(First_Log='min', Last_Log='max', N_Logs='count'\
                ).reset_index().sort_values(['N_Logs'], ascending=False), 
            right=gdf['device_details'].groupby(gdf['user_id']).first().reset_index(), 
            how="inner", 
            on='user_id'))
        print()

    # export to GeoPackage
    if export:
        try:
            schema = {
                'geometry': 'Point',
                'properties': {
                    'user_id': 'str',
                    'timestamp': 'datetime',
                    'accuracy': 'int',
                    'device_details': 'str',
                }
            }
            gdf.to_file(out_path, driver='GPKG', layer='gps_traces', schema=schema)
        except DriverIOError as e:
            print(e)
            print("ERROR: Output file path invalid")
    del gdf

# parse arguments and pass to function
if __name__ == '__main__':
    parser = ArgumentParser(description='Simple script to parse GPS data from Storage Connect into a GeoDataFrame and export to Shapefile.')
    parser.add_argument('-i', '--in_path', help='File Path for input file (*.json)', required=True)
    parser.add_argument('-o', '--out_path', help='File path for output file (*.gpkg)', required=False)
    parser.add_argument('-e', '--export', help='Export data to shalefile (True/False)', required=False)
    parser.add_argument('-r', '--report', help='Report number of per user (True/False)', required=False)
    parser.add_argument('-d', '--debug', help='Print out data that fail to parse (True/False)', required=False)
    args = vars(parser.parse_args())
    kwargs = {}
    for arg in args:
        if args[arg]:
            if args[arg].lower() in ['true', 'false']:
                kwargs[arg] = args[arg].lower() == 'true'
            else:
                kwargs[arg] = args[arg]
    parse_data(**kwargs)