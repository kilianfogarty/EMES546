import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import netCDF4 as nc4
import rasterio
from rasterio.transform import from_bounds
import geopandas as gpd
from rasterstats import zonal_stats
from shapely.geometry import box

pd.set_option("display.max_columns", None)  # show all columns when printing tables

# EDIT THESE PATHS to match where you saved the class data.
nc_file = r"C:\Users\Kilia\Desktop\EMES546\lectures\Lecture-12-Hazard-to-Building-Exposure\sfincs_map.nc"
buildings_file = r"C:\Users\Kilia\Desktop\EMES546\lectures\Lecture-12-Hazard-to-Building-Exposure\buildings_crop.shp"
nc = nc4.Dataset(nc_file)

# List the variables and dimensions stored in the file.
print(list(nc.variables.keys()))
print(list(nc.dimensions.keys()))

# Check the metadata associated with the water-surface variable.
if "zsmax" in nc.variables:
    v = nc.variables["zsmax"]
    print(v.dimensions, v.shape)
    print({k: v.getncattr(k) for k in v.ncattrs()})

# The CRS variable describes the coordinate reference system.
if "crs" in nc.variables:
    v = nc.variables["crs"]
    print({k: v.getncattr(k) for k in v.ncattrs()})

nc.close()

def as_float(a):
    # Convert a (possibly masked) NetCDF array to float, with NaN for missing values.
    return np.ma.filled(np.ma.masked_invalid(a).astype("float64"), np.nan)

nc = nc4.Dataset(nc_file)

# Grid-cell centre coordinates and grid-corner coordinates.
x = as_float(nc.variables["x"][:])
y = as_float(nc.variables["y"][:])
corner_x = as_float(nc.variables["corner_x"][:])
corner_y = as_float(nc.variables["corner_y"][:])

# Read the modelled ground/bed elevation.
zb_data = as_float(nc.variables["zb"][:])

nc.close()

# Check array dimensions and coordinate ranges.
print(zb_data.shape)
print(corner_x.shape)
print(corner_y.shape)
print(np.nanmin(corner_x), np.nanmax(corner_x))
print(np.nanmin(corner_y), np.nanmax(corner_y))

# These dimensions correspond to the supplied Florence model grid.
# The corner coordinates define the real-world bounds of the raster.
NROWS, NCOLS = 585, 872
CRS = "EPSG:32618"

xmin, xmax = np.nanmin(corner_x), np.nanmax(corner_x)
ymin, ymax = np.nanmin(corner_y), np.nanmax(corner_y)

# Affine transform: maps (row, col) to (easting, northing) with north at the top.
transform = from_bounds(xmin, ymin, xmax, ymax, NCOLS, NROWS)
extent = (xmin, xmax, ymin, ymax)  # real-world bounds, used for plotting

# NetCDF array order differs from the raster's row order.
# Python already reads the array as (rows, cols), so we only need to reverse
# the rows so north is at the top. (If the array arrives as (cols, rows),
# transpose it first.)
def to_raster_array(a):
    if a.shape == (NCOLS, NROWS):
        a = a.T
    assert a.shape == (NROWS, NCOLS), f"Unexpected grid shape {a.shape}"
    return np.flipud(a)

zb_r = to_raster_array(zb_data)

print(zb_r.shape)
print("Cell size (m):", (xmax - xmin) / NCOLS, "x", (ymax - ymin) / NROWS)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(zb_r, extent=extent, cmap="terrain")
ax.set(title="SFINCS Bed Elevation", xlabel="Easting (m)", ylabel="Northing (m)")
fig.colorbar(im, ax=ax, label="Elevation (m)")
plt.show()

nc = nc4.Dataset(nc_file)
zsmax_data = as_float(nc.variables["zsmax"][:])
nc.close()

# Confirm the array dimensions. The first dimension is the layer index
# for the supplied file; if your dimensions differ, stop and ask for help.
print(zsmax_data.shape)

if zsmax_data.shape[1:] not in [(NROWS, NCOLS), (NCOLS, NROWS)]:
    if zsmax_data.shape[:2] in [(NROWS, NCOLS), (NCOLS, NROWS)]:
        zsmax_data = np.moveaxis(zsmax_data, -1, 0)  # move layer axis to the front
    else:
        raise ValueError("Unexpected zsmax dimensions - stop and ask for help.")

n_layers = zsmax_data.shape[0]

# Convert each NetCDF layer to a raster array, keeping the same orientation
# used for the bed-elevation raster. Result shape: (layers, rows, cols).
zsmax_r = np.stack([to_raster_array(zsmax_data[i]) for i in range(n_layers)])

print(zsmax_r.shape)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(zsmax_r[0], extent=extent, cmap="viridis")
ax.set(title="Water-Surface Elevation: First Layer",
       xlabel="Easting (m)", ylabel="Northing (m)")
fig.colorbar(im, ax=ax, label="Water-surface elevation (m)")
plt.show()

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN cells
    zs_max_all = np.nanmax(zsmax_r, axis=0)

# Water depth = maximum water-surface elevation - ground elevation.
depth_raw = zs_max_all - zb_r

# For this activity, use a 0.15 m threshold to avoid counting very
# shallow values or numerical noise as meaningful inundation.
# Sub-threshold depths (including negative values) are set to NaN (R's NA).
max_depth = np.where(depth_raw >= 0.15, depth_raw, np.nan)

# Make a map where only flooded cells are shown.
flood_extent = np.where(max_depth > 0, 1.0, np.nan)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(max_depth, extent=extent, cmap="Blues",
               vmin=0, vmax=np.nanmax(max_depth))
ax.set(title="Maximum Flood Depth (m; depths < 0.15 m set to NA)",
       xlabel="Easting (m)", ylabel="Northing (m)")
fig.colorbar(im, ax=ax, label="Depth (m)")
plt.show()

fig, ax = plt.subplots(figsize=(8, 6))
ax.imshow(flood_extent, extent=extent, cmap=ListedColormap(["steelblue"]))
ax.set(title="Maximum Flood Extent (0.15 m threshold)",
       xlabel="Easting (m)", ylabel="Northing (m)")
plt.show()


# PART 3:

buildings = gpd.read_file(buildings_file)

# Check the geometry, coordinate reference system, and attributes.
print(buildings)
print(buildings.crs)
print(list(buildings.columns))
print(buildings.drop(columns="geometry").head())

if buildings.crs is None or buildings.crs != CRS:
    buildings = buildings.to_crs(CRS)

# Keep buildings within the modeled raster extent.
# (clip trims the polygons to the extent, like terra's crop.)
buildings_crop = gpd.clip(buildings, box(xmin, ymin, xmax, ymax)).reset_index(drop=True)

# Plot the flood extent, then overlay building outlines.
fig, ax = plt.subplots(figsize=(8, 6))
ax.imshow(flood_extent, extent=extent, cmap=ListedColormap(["lightblue"]))
buildings_crop.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=0.5)
ax.set(title="Building Footprints and Modeled Flood Extent",
       xlabel="Easting (m)", ylabel="Northing (m)")
plt.show()

# Helper: value of the raster cell containing each (x, y) point (NaN if outside).
def sample_raster(raster, xs, ys):
    cols = np.floor((xs - xmin) / (xmax - xmin) * NCOLS).astype(int)
    rows = np.floor((ymax - ys) / (ymax - ymin) * NROWS).astype(int)
    ok = (rows >= 0) & (rows < NROWS) & (cols >= 0) & (cols < NCOLS)
    out = np.full(len(xs), np.nan)
    out[ok] = raster[rows[ok], cols[ok]]
    return out

# Helper: summary statistic ("mean" or "max") of the raster cells under each
# building polygon, ignoring NaN cells. Cells whose centers fall inside the
# footprint are used; footprints too small to contain a cell center fall back
# to the single cell under the footprint.
def extract_stat(raster, polys, stat):
    res = zonal_stats(polys.geometry, raster.astype("float64"), affine=transform,
                      stats=[stat], nodata=np.nan, all_touched=False)
    vals = np.array([r[stat] if r[stat] is not None else np.nan for r in res],
                    dtype=float)
    missing = np.isnan(vals)
    if missing.any():
        pts = polys.geometry[missing].representative_point()
        vals[missing] = sample_raster(raster, pts.x.values, pts.y.values)
    return vals

# Mean depth across the building footprint.
buildings_crop["flood_depth_mean"] = extract_stat(max_depth, buildings_crop, "mean")

# Maximum depth across the building footprint.
buildings_crop["flood_depth_max"] = extract_stat(max_depth, buildings_crop, "max")

# Maximum water-surface elevation across the building footprint.
buildings_crop["zs_max"] = extract_stat(zs_max_all, buildings_crop, "max")

# Optional comparison: sample depth at each building's centroid.
building_centroids = buildings_crop.geometry.centroid
buildings_crop["flood_depth_centroid"] = sample_raster(
    max_depth, building_centroids.x.values, building_centroids.y.values)

print(buildings_crop.drop(columns="geometry").head())

# Summary statistics and missing values.
cols = [c for c in ["flood_depth_mean", "flood_depth_max", "flood_depth_centroid",
                    "zs_max", "FFE", "BLDG_VALUE"] if c in buildings_crop.columns]
print(buildings_crop[cols].describe())
print(buildings_crop[cols].isna().sum())

# Counts by occupancy category, if the field is present.
if "OCCUP_TYPE" in buildings_crop.columns:
    print(buildings_crop["OCCUP_TYPE"].value_counts(dropna=False))

# Counts by mapped flood-zone code, if the field is present.
if "FLD_ZONE" in buildings_crop.columns:
    print(buildings_crop["FLD_ZONE"].value_counts(dropna=False))

    # Total buildings in the cropped study area.
n_buildings = len(buildings_crop)

# Buildings with at least one intersecting cell at or above the depth threshold.
# (NaN > 0 is False, so buildings with no flooded cells are excluded.)
exposed_buildings = buildings_crop[buildings_crop["flood_depth_max"] > 0]

n_exposed = len(exposed_buildings)
fraction_exposed = n_exposed / n_buildings

print(n_buildings)
print(n_exposed)
print(fraction_exposed)

# This is the inventory value associated with exposed buildings.
# It is NOT the estimated flood damage.
print(exposed_buildings["BLDG_VALUE"].sum(skipna=True))