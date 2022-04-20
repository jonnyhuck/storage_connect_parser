# Storage Connect Parser
Simple processing script for data collected from GPS Tracker application.  
Converts the JSON dataset from StorageConnect into a Geopackage for analysis in GIS.

Simple Usage:
```bash
python sc2shp.py -i "./Export2022-04-19T16-23-09.json" -o "./gps_traces.gpkg"
```

Full set of usage parameters:
* `-i` `--in_path` File Path for input file downloaded from Storage Connect (*.json)
* `-o` `--out_path` File path for output file (*.gpkg)
* `-e` `--export` Export data to shalefile (True/False)
* `-r` `--report` Report number of per user (True/False)
* `-d` `--debug` Print out data that fail to parse (True/False)
