from utils import load_data, prepare_time_bins, create_color_map
from animator import animate_vessels

def main():
    csv_path = "Mergeddata/ais_201901.csv"
    mmsi_col = "mmsi"
    time_col = "datetime"
    interval = "5min"
    fps = 5
    bbox = [-60.103, -57.913, 45.468, 46.732]
    fading_trail = True  # if False, all tracks persist
    fade_minutes = 60  # Only applies if fading_trail is True

    df, duckdb_conn = load_data(csv_path, mmsi_col, time_col, interval, filter_date='2019-01-20')
    time_bins = prepare_time_bins(df, interval)
    color_map = create_color_map(df[mmsi_col].unique())

    animate_vessels(
        df=df,
        duckdb_conn=duckdb_conn,
        time_bins=time_bins,
        color_map=color_map,
        mmsi_col=mmsi_col,
        time_col=time_col,
        bbox=bbox,
        trail=fading_trail,
        fade_minutes=fade_minutes,
        interval_ms=200,
        fps=fps,
        output="vessel_tracks.gif"
    )

if __name__ == "__main__":
    main()
