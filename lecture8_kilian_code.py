import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

vmax = 75
u = 1 + (vmax - 35) / 33

# Question 1
# It is the z score standardization formula. It is the normalized vmax

t0 = -1.1 + 3.96 * u
tm = -1.60 + 4.80 * u

rm = 64.5 - 13.0 * u
re = 150 - 16.0 * u

# Question 2
# As u increases the maximum rainfall rate increases
# Maximum rainfall decreases
# Exponential decay length decreases


# Radial distance from hurricane center
r = np.arange(0, 501, 1)

# R-CLIPER rainfall rate
rain_rate = np.where(r < rm, t0 + (tm - t0) * (r / rm), tm * np.exp(-(r - rm) / re))

rain_profile = pd.DataFrame({"r": r, "rain_rate": rain_rate})

plt.figure(figsize=(8, 5))

plt.plot(rain_profile["r"], rain_profile["rain_rate"], linewidth=1)

plt.xlabel("Distance from hurricane center (km)")
plt.ylabel("Rainfall rate (mm/hr)")
plt.title(f"R-CLIPER Rainfall Profile: {vmax} kt")

plt.grid(False)
plt.tight_layout()
plt.show()

# Question 3
# Rainfall reaches its maximum at 35km, where r = rm
# Because the eye of the hurricane is calmer than the area surrounding it
# The rate of the rainfall decreases as we move away from the area of maximum rainfall

x = np.arange(-300, 301, 5)
y = np.arange(-300, 301, 5)

grid_x, grid_y = np.meshgrid(x, y)

grid = pd.DataFrame({"x": grid_x.ravel(), "y": grid_y.ravel()})

# Distance from hurricane center
grid["r"] = np.sqrt(grid["x"] ** 2 + grid["y"] ** 2)

grid["rain_rate"] = np.where(
    grid["r"] < rm,
    t0 + (tm - t0) * (grid["r"] / rm),
    tm * np.exp(-(grid["r"] - rm) / re),
)

plt.figure(figsize=(8, 8))

plt.pcolormesh(
    grid_x,
    grid_y,
    grid["rain_rate"].to_numpy().reshape(grid_y.shape),
    shading="auto",
    cmap="rainbow",
)

plt.gca().set_aspect("equal")

plt.xlabel("Distance east/west (km)")
plt.ylabel("Distance north/south (km)")
plt.colorbar(label="Rainfall\n(mm/hr)")
plt.title(f"2D R-CLIPER Rainfall Field: {vmax} kt")

plt.tight_layout()
plt.show()

# Question 4
# Because it is a symemtrical, parametric model.
# This assumes that there is no difference in rainfall based on geographic location, rather just your radius from the storm
# Orographic conditions, be it mountains or existing winds aloft.

track = pd.DataFrame(
    {"time": np.arange(0, 31, 1), "x_center": np.arange(-300, 301, 20), "y_center": 0}
)

print(track)

location_x = 0
location_y = 0

track["r"] = np.sqrt(
    (location_x - track["x_center"]) ** 2 + (location_y - track["y_center"]) ** 2
)

track["rain_rate"] = np.where(
    track["r"] < rm,
    t0 + (tm - t0) * (track["r"] / rm),
    tm * np.exp(-(track["r"] - rm) / re),
)

plt.figure(figsize=(8, 5))

plt.plot(track["time"], track["rain_rate"], linewidth=1)

plt.xlabel("Time (hours)")
plt.ylabel("Rainfall rate (mm/hr)")
plt.title("Rainfall at a Fixed Location")

plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.show()

# Question 5
# The rainfall increaseas as the peak radius gets closer then reduces as you pass through the
# band with the highest rainfall and the outer bands move over you.
# Around 13 and 17 hours
# It is directly related to that radius. The maximum rainfall occurs at that radius.

dt = 1
track["rain_total"] = track["rain_rate"] * dt
rain_total_sum = sum(track["rain_total"])

print(rain_total_sum)

# Question 6
# The accumulated rainfall is more important since it is the toal volume of water,
# when infrastructure and the environment reach their limits.

domain = pd.DataFrame({"x": np.arange(-400, 401, 10), "y": np.arange(-300, 301, 10)})
dt = 1
domain["rain_total"] = 0
for i in range(len(track)):
    r = np.sqrt(
        (domain["x"] - track["x_center"][i]) ** 2
        + (domain["y"] - track["y_center"][i]) ** 2
    )

    rain = np.where(r < rm, t0 + (tm - t0) * (r / rm), tm * np.exp(-(r - rm) / re))

    domain["rain_total"] = domain["rain_total"] + rain * dt

plt.figure(figsize=(8, 8))

plt.pcolormesh(
    x,
    y,
    domain["rain_total"].to_numpy().reshape(domain_y.shape),
    shading="auto",
    cmap="rainbow",
)

plt.gca().set_aspect("equal")

plt.xlabel("Distance east/west (km)")
plt.ylabel("Distance north/south (km)")
plt.colorbar(label="Total rainfall\n(mm)")
plt.title(f"Accumulated Rainfall: {vmax} kt")

plt.tight_layout()
plt.show()
