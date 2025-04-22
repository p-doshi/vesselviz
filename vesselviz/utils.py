import duckdb
import pandas as pd
import numpy as np
from matplotlib import cm, colors

def load_data(csv_path, mmsi_col, time_col, interval='5min', filter_date=None):
    df = pd.read_csv(csv_path, low_memory=False, parse_dates=[time_col])
    if filter_date:
        df = df[df[time_col].dt.date == pd.to_datetime(filter_date).date()].copy()
    df['time_bin'] = df[time_col].dt.floor(interval)
    
    conn = duckdb.connect(database=':memory:')
    conn.register("df", df)
    conn.execute("CREATE TABLE ais AS SELECT * FROM df")
    return df, conn

def prepare_time_bins(df, interval='5min'):
    start_time = df['time_bin'].min()
    end_time = df['time_bin'].max()
    return pd.date_range(start=start_time, end=end_time, freq=interval)

def create_color_map(unique_ids):
    norm = colors.Normalize(vmin=min(unique_ids), vmax=max(unique_ids))
    cmap = cm.get_cmap('viridis', 256)
    return {uid: cmap(norm(uid)) for uid in unique_ids}
