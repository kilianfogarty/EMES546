"""Hurricane Florence (2018) - R-CLIPER rainfall model (Python port of the main R script)."""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from m_lldist import m_lldist_L
from r_cliper import R_CLIPER

# ---- 1. Load IBTrACS North Atlantic data ----
IBTRACS_PATH = "/Users/Kilia/Desktop/EMES546/homework_2/IBTrACS.NA.list.v04r01.lines/IBTrACS.NA.list.v04r01.lines.shp"
ibtracs = gpd.read_file(IBTRACS_PATH)

# ---- 2. Extract Hurricane Florence ----
florence_sid = "2018242N13343"

florence = ibtracs[ibtracs["SID"] == florence_sid].copy()
florence["time"] = pd.to_datetime(florence["ISO_TIME"], utc=True)
florence["tclon"] = pd.to_numeric(florence["LON"], errors="coerce")
florence["tclat"] = pd.to_numeric(florence["LAT"], errors="coerce")
florence["Vmax"] = pd.to_numeric(florence["USA_WIND"], errors="coerce")
florence["pressure"] = pd.to_numeric(florence["USA_PRES"], errors="coerce")

florence = (
    florence.sort_values("time")
    .dropna(subset=["tclon", "tclat", "Vmax"])[
        ["time", "tclon", "tclat", "Vmax", "pressure"]
    ]
    .reset_index(drop=True)
)
n = len(florence)

# Check states

states = gpd.read_file(
    "C:/Users/Kilia/Desktop/EMES546/homework_2/cb_2018_us_state_20m.zip"
)

fig, ax = plt.subplots(figsize=(8, 6))
states.plot(ax=ax, color="lightgray", edgecolor="white")
ax.plot(florence["tclon"], florence["tclat"], "-", color="gray", lw=1)
sc = ax.scatter(
    florence["tclon"], florence["tclat"], c=florence["Vmax"], cmap="plasma", s=15
)
plt.colorbar(sc, label="USA_WIND (kt)")
ax.set_xlim(-100, -60)  # states file includes Alaska/Hawaii, so zoom in
ax.set_ylim(10, 50)
ax.set_title("Hurricane Florence (2018) IBTrACS track")
plt.show()

# That is the right track after looking at paths from news soureces online

# ---- 3. Time step (hours between successive fixes; first is 0) ----
timestep = np.zeros(n)
if n > 1:
    timestep[1:] = florence["time"].diff().dt.total_seconds().to_numpy()[1:] / 3600

# ---- 4. Storm translation distance / speed ----
if n > 1:
    distance = m_lldist_L(florence["tclon"], florence["tclat"])
    florence["translation_km"] = np.r_[np.nan, distance["dist"]]
    with np.errstate(divide="ignore", invalid="ignore"):
        florence["translation_kmh"] = np.r_[np.nan, distance["dist"] / timestep[1:]]
else:
    florence["translation_km"] = np.nan
    florence["translation_kmh"] = np.nan

# ---- 5. Rainfall model grid (0.5 degree) ----
inc = 0.5
lon = np.arange(-91, -68 + inc / 2, inc)  # inclusive of end, like R's seq()
lat = np.arange(23, 43 + inc / 2, inc)

# indexing="ij" -> arrays shaped (len(lon), len(lat)), matching R's lon x lat matrix
longrid, latgrid = np.meshgrid(lon, lat, indexing="ij")

# ---- 6. R-CLIPER rainfall at every track position ----
# Dimensions: longitude x latitude x time ; units: mm per time step
rainfall_RCLIPER = np.zeros((len(lon), len(lat), n))
print(rainfall_RCLIPER.shape)

for i in range(1, n):  # R's 2:nrow  ->  Python 1..n-1
    # NOTE: the R script multiplies by 1.94384 (m/s -> knots). IBTrACS USA_WIND is
    # already in knots, so check whether this conversion is really wanted.
    rgrid = R_CLIPER(
        longrid,
        latgrid,
        Vmax=florence.loc[i, "Vmax"] * 1.94384,
        tclat=florence.loc[i, "tclat"],
        tclon=florence.loc[i, "tclon"],
    )

    # inches/day -> inches over the time step -> mm
    rainfall_RCLIPER[:, :, i] = rgrid * (timestep[i] / 24) * 25.4

# ---- 8. Plot the rainfall at time step 30 ----
# You will need to figure this out!

# ---- 8. Plot the rainfall rate at time step 30 ----
step = 29  # R's time step 30 is index 29 in Python (0-based)

# mm accumulated during the step -> mm/hr
rate_mmhr = rainfall_RCLIPER[:, :, step] / timestep[step]

fig, ax = plt.subplots(figsize=(8, 6))
states.plot(ax=ax, color="lightgray", edgecolor="white")

# contourf wants Z shaped (len(lat), len(lon)), so transpose
cf = ax.contourf(lon, lat, rate_mmhr.T, levels=15, cmap="viridis", alpha=0.8)
plt.colorbar(cf, label="Rainfall rate (mm/hr)")

# mark the storm center at this time step
ax.plot(
    florence.loc[step, "tclon"],
    florence.loc[step, "tclat"],
    "r*",
    markersize=15,
    label="Storm center",
)

ax.set_xlim(min(lon.min(), florence["tclon"].min()) - 5, lon.max() + 5)
ax.set_ylim(lat.min(), lat.max())
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title(
    f"R-CLIPER rainfall rate, time step 30 ({florence.loc[step, 'time']:%Y-%m-%d %H:%M} UTC)"
)
ax.legend()
plt.show()

step = 29  # time step 30
print(florence.loc[step, ["time", "tclon", "tclat", "Vmax"]])

# It looks like it is still way out in the Atlantic at this point, so no land fall.
# That is why the plot looks funny. I will include an image of Florence's track in my PDF.


# ---- 9. Storm-total accumulated rainfall ----
total_rainfall = np.nansum(rainfall_RCLIPER, axis=2)  # shape (lon, lat)

# ---- 10. Plot accumulated R-CLIPER rainfall ----
fig, ax = plt.subplots(figsize=(9, 6))
states.plot(ax=ax, color="lightgray", edgecolor="white")

# total_rainfall is (lon, lat); contourf wants (lat, lon), so transpose
cf = ax.contourf(lon, lat, total_rainfall.T, levels=15, cmap="viridis", alpha=0.8)
plt.colorbar(cf, label="Accumulated rainfall (mm)")

# overlay the Florence track
ax.plot(florence["tclon"], florence["tclat"], "r-", lw=1.5, label="Florence track")
ax.scatter(florence["tclon"], florence["tclat"], c="red", s=8)

ax.set_xlim(lon.min(), lon.max())
ax.set_ylim(lat.min(), lat.max())
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Hurricane Florence (2018): R-CLIPER storm-total rainfall")
ax.legend()
plt.show()

# Part II, question 3: maximum accumulation
imax = np.unravel_index(np.argmax(total_rainfall), total_rainfall.shape)
print(
    f"Max R-CLIPER accumulation: {total_rainfall.max():.1f} mm "
    f"({total_rainfall.max() / 25.4:.1f} in) at "
    f"lon={lon[imax[0]]:.1f}, lat={lat[imax[1]]:.1f}"
)
