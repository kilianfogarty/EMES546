import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# This should be the path to your storm path shape file
storms = gpd.read_file(
    "/Users/Kilia/Desktop/EMES546/homework_1/IBTrACS.NA.list.v04r01.lines/IBTrACS.NA.list.v04r01.lines.shp"
)

# This should be the path to your states shape file
states = gpd.read_file("/Users/Kilia/Desktop/EMES546/homework_1/s_18mr25/s_18mr25.shp")

# switch states CRS to storm's version
states_wgs84 = states.to_crs(storms.crs)

coastal_states = [
    "ME",
    "NH",
    "MA",
    "RI",
    "CT",
    "NY",
    "NJ",
    "DE",
    "MD",
    "VA",
    "NC",
    "SC",
    "GA",
    "FL",
    "MS",
    "AL",
    "LA",
    "TX",
]

states_wgs84 = states_wgs84[states_wgs84["STATE"].isin(coastal_states)].copy()

# I am using the hint to use Landfall
landfalls = storms[storms["USA_RECORD"] == "L"].copy()

# Convert ISO_TIME to datetime
landfalls["ISO_TIME"] = pd.to_datetime(landfalls["ISO_TIME"])

# Extract year
landfalls["year"] = landfalls["ISO_TIME"].dt.year

print("Number of U.S. landfall records:", len(landfalls))
print("Number of unique landfalling storms:", landfalls["SID"].nunique())

# Question 1
landfall_states = gpd.sjoin(
    landfalls, states_wgs84[["STATE", "geometry"]], how="inner", predicate="intersects"
)

print(landfall_states[["SID", "STATE", "year"]].head())

landfalls_by_state = (
    landfall_states.groupby("STATE")["SID"].nunique().sort_values(ascending=False)
)

print("\nHistorical landfalls by state:")
print(landfalls_by_state)

landfall_table = landfalls_by_state.reset_index()

landfall_table.columns = ["State", "Landfalls"]

print(landfall_table)

# Question 2

annual_landfalls = landfalls.groupby("year")["SID"].nunique()

all_years = pd.RangeIndex(
    start=landfalls["year"].min(), stop=landfalls["year"].max() + 1
)

annual_landfalls = annual_landfalls.reindex(all_years, fill_value=0)

annual_landfalls.index.name = "Year"

print(annual_landfalls)

plt.figure(figsize=(14, 6))

plt.bar(annual_landfalls.index, annual_landfalls.values)

plt.xlabel("Year")
plt.ylabel("Number of Landfalls")
plt.title("Annual U.S. Gulf/Atlantic Tropical Cyclone Landfalls")

plt.show()

lambda_coast = annual_landfalls.mean()

print(f"Average annual arrival rate λ = {lambda_coast:.3f} storms/year")

# Question 3

wind = landfalls["USA_WIND"].dropna()

# Remove invalid/missing values
wind = wind[wind > 0]

print("Number of wind observations:", len(wind))
print(wind.describe())

plt.figure(figsize=(10, 6))

plt.hist(wind, bins=20, density=True, edgecolor="black")

plt.xlabel("Wind Speed (knots)")
plt.ylabel("Probability Density")
plt.title("Tropical Cyclone Wind Speed at U.S. Landfall")

plt.show()

# Fit Weibull distribution
weibull_shape, weibull_loc, weibull_scale = stats.weibull_min.fit(wind)

print("Weibull parameters:")
print("Shape:", weibull_shape)
print("Location:", weibull_loc)
print("Scale:", weibull_scale)

x = np.linspace(wind.min(), wind.max(), 500)

pdf = stats.weibull_min.pdf(x, weibull_shape, loc=weibull_loc, scale=weibull_scale)

plt.figure(figsize=(10, 6))

plt.hist(wind, bins=20, density=True, edgecolor="black", alpha=0.7)

plt.plot(x, pdf, linewidth=2, label="Weibull fit")

plt.xlabel("Wind Speed (knots)")
plt.ylabel("Probability Density")
plt.title("Landfall Wind Speed with Weibull Fit")
plt.legend()

plt.show()

# ---------------------------------------------------------
# QUESTION 4
# 10 REALIZATIONS OF 1000 YEARS
# ---------------------------------------------------------

n_years = 1000
n_realizations = 10

rng = np.random.default_rng(42)

realizations = []

for realization in range(n_realizations):
    # Number of storms in each year
    storms_per_year = rng.poisson(lambda_coast, n_years)

    annual_max = np.zeros(n_years)

    for year in range(n_years):
        n_storms = storms_per_year[year]

        if n_storms > 0:
            simulated_winds = stats.weibull_min.rvs(
                weibull_shape,
                loc=weibull_loc,
                scale=weibull_scale,
                size=n_storms,
                random_state=rng,
            )

            annual_max[year] = simulated_winds.max()

        else:
            annual_max[year] = 0

    realizations.append(annual_max)


def return_period_data(annual_max):

    # Remove years with no storm
    annual_max = annual_max[annual_max > 0]

    # Sort largest to smallest
    sorted_max = np.sort(annual_max)[::-1]

    n = len(sorted_max)

    # Empirical annual exceedance probability
    rank = np.arange(1, n + 1)

    aep = rank / (n + 1)

    # Return period
    return_period = 1 / aep

    return sorted_max, return_period


plt.figure(figsize=(10, 7))

for i, annual_max in enumerate(realizations):
    intensity, return_period = return_period_data(annual_max)

    plt.plot(intensity, return_period, label=f"Simulation {i + 1}")

plt.yscale("log")

plt.xlabel("Wind Speed (knots)")
plt.ylabel("Return Period (years)")
plt.title("Simulated Tropical Cyclone Wind Speed Return Periods")

plt.legend()

plt.show()


# Question 5

state = "FL"

fl_landfalls = landfall_states[landfall_states["STATE"] == state].copy()

fl_annual = fl_landfalls.groupby("year")["SID"].nunique()

# Use same historical time period as coastline
fl_annual = fl_annual.reindex(all_years, fill_value=0)

lambda_fl = fl_annual.mean()

print(f"Florida λ = {lambda_fl:.3f} storms/year")

fl_realizations = []

for realization in range(n_realizations):
    storms_per_year = rng.poisson(lambda_fl, n_years)

    annual_max = np.zeros(n_years)

    for year in range(n_years):
        n_storms = storms_per_year[year]

        if n_storms > 0:
            simulated_winds = stats.weibull_min.rvs(
                weibull_shape,
                loc=weibull_loc,
                scale=weibull_scale,
                size=n_storms,
                random_state=rng,
            )

            annual_max[year] = simulated_winds.max()

        else:
            annual_max[year] = 0

    fl_realizations.append(annual_max)

plt.figure(figsize=(10, 7))

# Coastline
for i, annual_max in enumerate(realizations):
    intensity, return_period = return_period_data(annual_max)

    plt.plot(intensity, return_period, alpha=0.3)


# Florida
for i, annual_max in enumerate(fl_realizations):
    intensity, return_period = return_period_data(annual_max)

    plt.plot(intensity, return_period, alpha=0.3)


plt.yscale("log")

plt.xlabel("Wind Speed (knots)")
plt.ylabel("Return Period (years)")

plt.title("Simulated Return Periods: U.S. Coastline vs Florida")

plt.show()
