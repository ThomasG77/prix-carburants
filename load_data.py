import sqlite3
import pandas as pd
import geopandas
from matplotlib import pyplot as plt

csv_stations = 'stations.csv'
csv_files_to_load = [
    'fermetures',
    'jour_and_horaires',
    'ouvertures',
    'prix',
    'ruptures',
    'services_text'
]

df_stations = pd.read_csv(csv_stations)
gdf_stations = geopandas.GeoDataFrame(
    df_stations, geometry=geopandas.points_from_xy(df_stations.longitude, df_stations.latitude))

gdf_stations.to_file("carburants.gpkg", layer='stations', driver="GPKG")

conn = sqlite3.connect("carburants.gpkg")

for csv_file_name in csv_files_to_load:
    df = pd.read_csv(f'{csv_file_name}.csv')
    df.to_sql(csv_file_name, conn, if_exists="replace")

conn.close()
