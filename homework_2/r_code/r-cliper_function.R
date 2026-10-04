# ============================================================
# FUNCTION 2
# R-CLIPER rainfall model
# ============================================================

R_CLIPER <- function(grid, Vmax, tclat, tclon) {
  
  # Inputs:
  #   longrid = matrix of longitude coordinates
  #   latgrid = matrix of latitude coordinates
  #   Vmax    = maximum sustained wind speed, knots
  #   tclat   = storm-center latitude
  #   tclon   = storm-center longitude
  #
  # Output:
  #   rgrid = rainfall rate, inches/day
  
  
  # ----------------------------------------------------------
  # NHC bias-adjusted R-CLIPER coefficients
  #
  # T0 = a1 + b1 * U
  # Tm = a2 + b2 * U
  # rm = a3 + b3 * U
  # re = a4 + b4 * U
  #
  # T0 and Tm: inches/day
  # rm and re: km
  # ----------------------------------------------------------
  
  #FILL IN THESE VALUES
  a1 <- 
  a2 <- 
  a3 <- 
  a4 <- 
  
  b1 <- 
  b2 <- 
  b3 <- 
  b4 <- 
  
  
  # ----------------------------------------------------------
  # Normalized intensity
  # ----------------------------------------------------------
  
  #Fill in this equation
  U <-
  
  
  # ----------------------------------------------------------
  # R-CLIPER parameters
  # ----------------------------------------------------------
  
  #Fill in these equations
  
  T0 <- 
  Tm <- 
  rm <- 
  re <- 
  
  
  # Avoid physically nonsensical negative model parameters
  # at very low intensities.
  rm <- max(rm, 1)
  re <- max(re, 1)
  
  
  # ----------------------------------------------------------
  # Distance from every grid point to storm center
  #
  # We use the same spherical-earth haversine formulation
  # as m_lldist_L(), but vectorized over the entire grid.
  # ----------------------------------------------------------
  
  earth_radius <- 6378.137  # km
  pifac <- pi / 180
  
  #location in the grid
  lat1 <- grid$y * pifac
  lon1 <- grid$x * pifac
  
  #location of the storm center
  lat2 <- tclat * pifac
  lon2 <- tclon * pifac
  
  #distance to the storm center
  dlat <- lat1 - lat2
  dlon <- lon1 - lon2
  
  a <- sin(dlat / 2)^2 +
    cos(lat1) * cos(lat2) *
    sin(dlon / 2)^2
  
  r <- earth_radius * 2 *
    asin(sqrt(pmin(1, a)))
  
  
  # ----------------------------------------------------------
  # Calculate rainfall rate
  #
  # r <= rm:
  #
  #   R = T0 + (Tm - T0) * r/rm
  #
  # r > rm:
  #
  #   R = Tm * exp[-(r-rm)/re]
  #
  # R-CLIPER is truncated at 800 km.
  # ----------------------------------------------------------
  
  rainfall <- numeric(length(r))
  
  # Inside radius of maximum rainfall
  inside <- r <= rm
  
  rainfall[inside] <-
    T0 +
    (Tm - T0) *
    r[inside] / rm
  
  # Outside radius of maximum rainfall
  outside <- r > rm & r <= 800
  
  rainfall[outside] <-
    Tm *
    exp(-(r[outside] - rm) / re)
  
  # Beyond 800 km
  rainfall[r > 800] <- 0
  
  # Return rainfall rate in inches/day
  rainfall
  
}