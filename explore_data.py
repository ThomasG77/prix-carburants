import sqlite3
import pandas as pd
import geopandas
from matplotlib import pyplot as plt

with sqlite3.connect("carburants.gpkg") as conn:
    # enable loading extensions and load spatialite
    conn.enable_load_extension(True)
    try:
        conn.load_extension('mod_spatialite.so')
    except sqlite3.OperationalError:
        conn.load_extension('libspatialite.so')

    print(conn.execute('SELECT spatialite_version()').fetchone()[0])
    # df_stations = pd.read_sql_query('select * from stations JOIN ruptures ON stations.id = ruptures.station_id', conn)
    df_stations = pd.read_sql_query(
        """select st_AsText(CastAutomagic(geom)) as geom_text,
        *, strftime('%Y-%m-%dT%H:%M:%S', debut) AS isoDateTime
        FROM stations
        JOIN ruptures
        ON stations.id = ruptures.station_id
        WHERE strftime('%Y-%m-%dT%H:%M:%S', debut)>= datetime('2022-09-01T00:00:00')
        ORDER BY strftime('%Y-%m-%dT%H:%M:%S', debut)
        """, conn)
    print(df_stations)
