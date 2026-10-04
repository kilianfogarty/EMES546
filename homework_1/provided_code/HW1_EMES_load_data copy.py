#EMES Homework 1 python version

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import scipy.stats 

#Load data

#Read in TC tracks

storms = gpd.read_file("/Users/aficca/Downloads/IBTrACS/IBTrACS.NA.list.v04r01.lines.shp")
print(storms.crs)

#keep only the segment of storm that makes landfall
landfall_seg = storms[storms["USA_RECORD"] == "L"].copy()

#Read in U.S. states and filter to states with a coast line on the Gulf/Atlantic
states = gpd.read_file("/Users/aficca/Downloads/s_18mr25/s_18mr25.shp")
print(states.crs)

#plot
states.plot()
plt.show()

#Transform shp2 to CRS of shp1
states_wgs84 = states.to_crs(storms.crs)

#FILTER TO ONLY STORMS OF INTEREST (THOSE THAT MAKE LANDFALL IN THE CONTINENTAL US)

#subset to coastal states
states_wgs84 = states_wgs84[
    states_wgs84["STATE"].isin(["ME", "NH", "MA", "RI", "CT", "NY", "NJ", "DE", "MD", "VA", "NC", "SC", "GA", "FL", "MS", "AL", "LA", "TX"])
]

#keep only the storms that make landfall in the US
select_storms = gpd.sjoin(
    storms,
    states_wgs84,
    how = "inner",
    predicate = "intersects"
)
us_storms = storms[
    storms["SID"].isin(select_storms["SID"])
].copy()

#how many unique storms have made landfall in the US
print(
    "Number of unique storms:",
    select_storms["SID"].nunique()
    )

#plot storms and state geometries
#Here I am only plotting the segments that overlap the states; you could also plot the whole track using us_storms
#optional: color each line segment by the storm's category on the Saffir-Simpson Scale
cat_colors = {-5: "grey", #unknown [xx]
              -4: "grey", #post-tropical [ex, et, pt]
              -3: "grey", #miscellaneous disturbances
              -2: "grey", #subtropical
              -1: "#5ebbff", #tropical depression (W<34)
              0: "#00f000", #tropical storm (34-64)
              1: "#ffff00", #category 1
              2: "#ffa500", #cat 2
              3: "#ff4500", #cat 3
              4: "#ff00ff", #cat 4
              5: "#9932cc" #cat 5
              }
fig, ax = plt.subplots(figsize=(12, 8))
states_wgs84.plot(
    ax=ax,
    facecolor="none",
    edgecolor="black"
)

for category, color in cat_colors.items():

    subset = select_storms[
        select_storms["USA_SSHS"] == category
    ]

    if not subset.empty:
        subset.plot(
            ax=ax,
            color=color,
            linewidth=0.8,
            label=str(category)
        )
plt.legend(title="USA_SSHS")
plt.title("Tropical Cyclone Tracks")
plt.show()