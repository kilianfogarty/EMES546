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

# ---- 9. Storm-total accumulated rainfall ----
total_rainfall = np.nansum(rainfall_RCLIPER, axis=2)  # shape (lon, lat)

# ---- 10. Plot accumulated R-CLIPER rainfall ----
# You will need to figure this out!
# Hint: plt.contourf(lon, lat, total_rainfall.T) and overlay florence.tclon / tclat
