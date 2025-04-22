import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import timedelta

def animate_vessels(df, duckdb_conn, time_bins, color_map, mmsi_col, time_col,
                    bbox, trail=True, fade_minutes=60, interval_ms=200, fps=5, output="vessel_tracks.gif"):
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150, subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent(bbox, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, zorder=0, edgecolor='black', facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, zorder=0, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=1)
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    time_text = ax.text(0.02, 0.97, '', transform=ax.transAxes, fontsize=12,
                        verticalalignment='top', bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))

    unique_mmsi = df[mmsi_col].unique()
    vessel_tracks = {m: [] for m in unique_mmsi}
    vessel_last_seen_frame = {m: -1 for m in unique_mmsi}
    labels_added = set()
    scatters, texts, track_lines, permanent_labels = [], [], [], []

    fade_frames = int((fade_minutes * 60) / (interval_ms / 1000))  # convert to frame count

    def update(frame_idx):
        t_start = time_bins[frame_idx]
        t_end = t_start + timedelta(minutes=5)

        for s in scatters: s.remove()
        for t in texts: t.remove()
        for line in track_lines: line.remove()
        scatters.clear()
        texts.clear()
        track_lines.clear()

        query = f"""
            WITH ranked AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY {mmsi_col}, time_bin ORDER BY {time_col} DESC) AS rn
                FROM ais
                WHERE time_bin = TIMESTAMP '{t_start}'
            )
            SELECT * FROM ranked WHERE rn = 1;
        """
        current_data = duckdb_conn.execute(query).fetchdf()

        for _, row in current_data.iterrows():
            mmsi, lon, lat = row[mmsi_col], row['lon'], row['lat']
            vessel_tracks[mmsi].append((frame_idx, lon, lat))
            vessel_last_seen_frame[mmsi] = frame_idx

            scat = ax.scatter(lon, lat, color=color_map[mmsi], s=20, zorder=5)
            scatters.append(scat)
            label = ax.text(lon + 0.01, lat + 0.01, str(mmsi), color='black', fontsize=7, weight='bold', zorder=6)
            texts.append(label)

        for mmsi, history in vessel_tracks.items():
            if trail:
                valid_points = [(lon, lat) for (f_idx, lon, lat) in history if frame_idx - f_idx <= fade_frames]
                vessel_tracks[mmsi] = [(f_idx, lon, lat) for (f_idx, lon, lat) in history if frame_idx - f_idx <= fade_frames]
            else:
                valid_points = [(lon, lat) for (f_idx, lon, lat) in history]

            if len(valid_points) > 1:
                lons, lats = zip(*valid_points)
                line, = ax.plot(lons, lats, color=color_map[mmsi], linewidth=1, alpha=0.6, zorder=2)
                track_lines.append(line)

        for mmsi in unique_mmsi:
            last_seen = vessel_last_seen_frame[mmsi]
            if last_seen >= 0 and frame_idx - last_seen >= 3 and mmsi not in labels_added:
                points = vessel_tracks[mmsi]
                if points:
                    _, lon, lat = points[-1]
                    perm_label = ax.text(lon + 0.01, lat + 0.01, str(mmsi), color='black', fontsize=7, zorder=7)
                    permanent_labels.append(perm_label)
                    labels_added.add(mmsi)

        time_text.set_text(f"Time: {t_start.strftime('%H:%M')} - {t_end.strftime('%H:%M')}")
        return scatters + texts + track_lines + [time_text] + permanent_labels

    ani = animation.FuncAnimation(fig, update, frames=len(time_bins), interval=interval_ms, blit=True)
    ani.save(output, writer="pillow", fps=fps)
    print(f"GIF saved as '{output}'")
