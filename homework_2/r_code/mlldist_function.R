# ============================================================
# FUNCTION 1
# Spherical-earth distance between lon/lat points
# ============================================================

m_lldist_L <- function(lon, lat) {
  
  # Inputs:
  #   lon = longitude(s), degrees
  #   lat  = latitude(s), degrees
  #
  # Output:
  #   dist = distance between successive points, km
  #
  # For two points, returns one distance.
  # For vectors, returns distances between successive points.
  
  pifac <- pi / 180
  earth_radius <- 6378.137  # km
  
  if (length(lon) < 2 || length(lat) < 2) {
    stop("lon and lat must each contain at least two values.")
  }
  
  lon1 <- lon[-length(lon)] * pifac
  lon2 <- lon[-1] * pifac
  
  lat1 <- lat[-length(lat)] * pifac
  lat2 <- lat[-1] * pifac
  
  dlon <- lon2 - lon1
  dlat <- lat2 - lat1
  
  a <- sin(dlat / 2)^2 +
    cos(lat1) * cos(lat2) * sin(dlon / 2)^2
  
  dist <- earth_radius *
    2 * asin(sqrt(pmin(1, a)))
  
  dx <- earth_radius *
    2 *
    asin(
      sqrt(
        pmax(
          0,
          cos(lat1) *
            cos(lat2) *
            sin(dlon / 2)^2
        )
      )
    ) *
    sign(dlon)
  
  dy <- earth_radius *
    2 *
    asin(
      sqrt(
        pmin(1, sin(dlat / 2)^2)
      )
    ) *
    sign(dlat)
  
  return(
    list(
      dist = dist,
      dx = dx,
      dy = dy
    )
  )
}


