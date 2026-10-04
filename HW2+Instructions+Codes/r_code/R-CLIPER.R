# ============================================================
# Hurricane Florence (2018) — R-CLIPER rainfall model
#
# This script calls TWO functions:
#   1. m_lldist_L() : spherical-earth distance calculation
#   2. R_CLIPER()   : R-CLIPER rainfall-rate calculation
#
# The main script:
#   - loads Florence's IBTrACS North Atlantic best-track data
#   - creates a 0.5-degree grid over which Florence tracks
#   - calculates rainfall for every IBTrACS time step
#   - converts rainfall rate (in/day) to accumulated rainfall (mm)
#   - plots storm-total R-CLIPER rainfall and the Florence track
#
# R-CLIPER coefficients below are the NHC bias-adjusted coefficients
# described by Tuleya et al. (2007).
# ============================================================

# ============================================================
# 0. Packages
# ============================================================

library("dplyr")
library("lubridate")
library("sf")
library("ggplot2")

# ============================================================
# 1. Load IBTrACS North Atlantic data
# ============================================================

#load your IBTrACS data here
ibtracs <- st_read()

# ============================================================
# 2. Extract Hurricane Florence
# ============================================================

# Florence 2018 IBTrACS storm identifier
florence_sid <- "2018242N13343"

florence <- ibtracs %>%
  filter(
    SID == florence_sid
  ) %>%
  mutate(
    time = ymd_hms(ISO_TIME),
    tclon = as.numeric(LON),
    tclat = as.numeric(LAT),
    Vmax = as.numeric(USA_WIND),
    pressure = as.numeric(USA_PRES)
  ) %>%
  arrange(time) %>%
  filter(
    !is.na(tclon),
    !is.na(tclat),
    !is.na(Vmax)
  ) %>%
  dplyr::select(
    time,
    tclon,
    tclat,
    Vmax,
    pressure
  )


# ============================================================
# 3. Calculate time step
# ============================================================

times <- florence$time

timestep <- rep(
  0,
  nrow(florence)
)

if (nrow(florence) > 1) {
  
  timestep[2:nrow(florence)] <-
    as.numeric(
      difftime(
        times[2:nrow(florence)],
        times[1:(nrow(florence) - 1)],
        units = "hours"
      )
    )
}


# ============================================================
# 4. Calculate storm translation distance
# ============================================================

if (nrow(florence) > 1) {
  
  #calculate the distance on the Earth's sphere
  distance <- m_lldist_L(
    florence$tclon,
    florence$tclat
  )
  
  florence$translation_km <- c(
    NA,
    distance$dist
  )
  
  florence$translation_kmh <- c(
    NA,
    distance$dist / timestep[-1]
  )
  
} else {
  
  florence$translation_km <- NA
  florence$translation_kmh <- NA
}

# ============================================================
# 5. Create a rainfall model grid
# ============================================================

inc <- 0.5

#you can change these values if you want to extend your plot!
lon <- seq(-91, -68, by = inc)
lat <- seq(23, 43, by = inc)

grid <- expand.grid(
  x = lon,
  y = lat
)

# ============================================================
# 6. Calculate R-CLIPER rainfall at every track position
# ============================================================

# Store accumulated rainfall for each time step.
#
# Dimensions:
#   longitude x latitude x time
#
# Units:
#   mm accumulated during each time step

#create an empty array to store the data
rainfall_RCLIPER <- array(
  0,
  dim = c(
    length(lon), #m
    length(lat), #n
    nrow(florence)
  )
)

#check that the dimensions make sense
dim(rainfall_RCLIPER)

#for each time step
for (i in 2:nrow(florence)) {
  
  # ----------------------------------------------------------
  # R-CLIPER rainfall rate
  # ----------------------------------------------------------
  
  #CALL THE R-CLIPER FUNCTION
  rgrid <- R_CLIPER(
    grid=grid,
    Vmax = florence$Vmax[i]*1.94384, #Vmax in knots
    tclat = florence$tclat[i],
    tclon = florence$tclon[i]
  )
  
  
  # ----------------------------------------------------------
  # Convert:
  #
  # inches/day
  #       ->
  # inches/hour
  #       ->
  # inches accumulated during timestep
  #       ->
  # millimeters accumulated during timestep
  # ----------------------------------------------------------
  
  rgrid_mm <- rgrid *
    (timestep[i] / 24) *
    25.4
  
  # Convert vector back to longitude × latitude matrix
  rgrid_matrix <- matrix(
    rgrid_mm,
    nrow = length(lon),
    ncol = length(lat)
  )
  
  rainfall_RCLIPER[ , , i] <- rgrid_matrix
}


# ============================================================
# 8. Plot the rainfall rate at time step 30
# ============================================================

#You will need to figure this out!

# ============================================================
# 9. Storm-total accumulated rainfall
# ============================================================

total_rainfall <- apply(
  rainfall_RCLIPER,
  c(1, 2),
  sum,
  na.rm = TRUE
)

# ============================================================
# 10. Plot accumulated R-CLIPER rainfall
# ============================================================

#You will need to figure this out!

# ============================================================
# End of script
# ============================================================
