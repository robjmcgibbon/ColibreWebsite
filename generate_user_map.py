import os
import re

# This was created using bokeh 3.8
from bokeh.models import ColumnDataSource, WheelZoomTool, HoverTool, CustomJS, Scatter
from bokeh.plotting import figure, save
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import xyzservices.providers as xyz

def extract_svg_path(svg_filename):
    """
    Extracts the 'd' path data from an SVG file.
    """
    # Parse SVG XML
    tree = ET.parse(svg_filename)
    root = tree.getroot()

    # Handle namespace if present
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    paths = root.findall(".//svg:path", ns)
    if not paths:
        # fallback if namespace not used
        paths = root.findall(".//path")

    # Extract all 'd' attributes
    d_values = [p.attrib.get("d") for p in paths if "d" in p.attrib]
    if not d_values:
        raise ValueError(f"No path data found in {svg_filename}")

    # Combine multiple paths into one continuous path
    combined_path = " ".join(d_values)

    return combined_path


def generate_user_map():
    # Read in data
    df = pd.read_csv('src/colibre_users.txt', sep=r'\s+')


    # Combine names for same affiliation
    def sort_by_surname(names):
        return sorted(names, key=lambda n: n.split(' ', 1)[1] if ' ' in n else n)

    df = (
        df.groupby('Affiliation', as_index=False)
          .agg({
              'Name': lambda x: '\n'.join(sort_by_surname(x)),
              'Latitude': 'median',
              'Longitude': 'median'
          })
          .rename(columns={'Name': 'Names'})
    )

    # Convert latitude & longitde to metcator coordinates
    def wgs84_to_web_mercator(lon, lat):
        k = 6378137
        x = lon * (k * np.pi/180.0)
        y = np.log(np.tan((90 + lat) * np.pi/360.0)) * k
        return x, y
    df["x"], df["y"] = wgs84_to_web_mercator(df["Longitude"], df["Latitude"])

    # Set map bounds
    min_lon, max_lon = -180, 180
    min_lat, max_lat = -56, 70
    min_x, min_y = wgs84_to_web_mercator(min_lon, min_lat)
    max_x, max_y = wgs84_to_web_mercator(max_lon, max_lat)

    # Create map
    p = figure(
        x_range=(min_x, max_x),
        y_range=(min_y, max_y),
        x_axis_type="mercator", y_axis_type="mercator",
        title=None,
        sizing_mode="scale_width",
        aspect_ratio=1.9,
    )
    # CARTO require an API key for their basemaps (free, see README).
    # Without a valid key the tiles are silently watermarked 'API KEY REQUIRED'.
    tile_provider = xyz.CartoDB.VoyagerNoLabels.copy()
    with open('CARTO_key', 'r') as file:
        tile_provider['url'] += '?key=' + file.read().strip()
    p.add_tile(tile_provider)

    logo_path = extract_svg_path("src/assets/logo.svg")

    logo_marker = CustomJS(
        code=f"""
        export default (args, obj, {{ctx, i, r, visuals}}) => {{
            const path = new Path2D("{logo_path}")

            // --- IMPORTANT ---
            // Find the viewBox="x y w h" in your "drawing.svg" file
            // and set these constants to w and h.
            const SVG_WIDTH = 2500;
            const SVG_HEIGHT = 1957;
            // ---

            // Calculate scale factor to fit the SVG inside the 'size'
            const scale = (2 * r) / Math.max(SVG_WIDTH, SVG_HEIGHT);

            ctx.save();

            // Apply the scaling
            ctx.scale(scale, scale);

            // Translate to center the marker.
            // We want the SVG's center (SVG_WIDTH/2, SVG_HEIGHT/2)
            // to be at the data point (0,0), so we translate
            // by the negative of that.
            ctx.translate(-SVG_WIDTH / 2, -SVG_HEIGHT / 2);

            // Apply fill/line styles from the scatter call (e.g., fill_alpha)
            visuals.fill.apply(ctx, i);
            visuals.line.apply(ctx, i);

            // Draw the path
            ctx.fill(path);
            // ctx.stroke(path); // Uncomment if you also want an outline

            ctx.restore();

            // Do not return anything, as we are drawing directly
        }}
        """
    )

    # Plot users
    source = ColumnDataSource(df)
    p.scatter(
        x="x",
        y="y",
        size=50,
        fill_alpha=0.8,
        fill_color="black",
        source=source,
        marker="@logo",
        defs={"@logo": logo_marker},
    )

    # Add information for hover
    hover = HoverTool(tooltips="""
        <div style="white-space: pre-line;">
            <span style="color:#1f77b4; font-weight:bold;">Institute:</span><br> @Affiliation
            <span style="color:#1f77b4; font-weight:bold;">Project leads:</span><br> @Names
        </div>
    """)
    p.add_tools(hover)

    # Remove the default grid lines
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None

    # Activate wheel zoom
    for tool in p.tools:
        if isinstance(tool, WheelZoomTool):
            p.toolbar.active_scroll = tool
            break

    # Apply bounds to the plot ranges
    p.x_range.bounds = (min_x, max_x)
    p.y_range.bounds = (min_y, max_y)

    # Zoom level limit
    p.x_range.min_interval = 10**5.5
    p.x_range.max_interval = max_x - min_x
    p.y_range.min_interval = 10**5.5
    p.y_range.max_interval = max_y - min_y

    # Save
    save(p, 'src/assets/team/user_map.html', title='COLIBRE Users', resources='inline')

if __name__ == '__main__':
    generate_user_map()

