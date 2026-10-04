"""R-CLIPER rainfall model (Python port of R_CLIPER)."""

import numpy as np

EARTH_RADIUS_KM = 6378.137


def R_CLIPER(longrid, latgrid, Vmax, tclat, tclon):
    """Rainfall rate (inches/day) on a lon/lat grid around a storm center.

    Parameters
    ----------
    longrid, latgrid : arrays of identical shape (degrees)
    Vmax  : maximum sustained wind, knots
    tclat, tclon : storm-center latitude/longitude, degrees

    Returns
    -------
    rainfall : array, same shape as longrid, inches/day
    """
    longrid = np.asarray(longrid, dtype=float)
    latgrid = np.asarray(latgrid, dtype=float)

    # ---- NHC bias-adjusted R-CLIPER coefficients (Tuleya et al. 2007) ----
    # T0 = a1 + b1*U ; Tm = a2 + b2*U ; rm = a3 + b3*U ; re = a4 + b4*U
    # T0, Tm: inches/day ; rm, re: km
    # FILL IN THESE VALUES (left blank in the original R script too)

    # I PULLED THESE VALUES FROM THE IN CLASS HTML FROM LEC 8
    # a is intercept, b is slope

    a1 = -1.1
    a2 = -1.6
    a3 = 64.5
    a4 = 150
    b1 = 3.96
    b2 = 4.8
    b3 = -13
    b4 = -16

    # ---- Normalized intensity ----

    # idk if this should be int or float, I'm guessing float

    U = 1 + (Vmax - 35) / 33

    # ---- R-CLIPER parameters ----
    T0 = a1 + b1 * U
    Tm = a2 + b2 * U
    rm = a3 + b3 * U
    re = a4 + b4 * U

    # Avoid negative/zero parameters at very low intensities
    rm = max(rm, 1)
    re = max(re, 1)

    # ---- Haversine distance from each grid point to the storm center ----
    pifac = np.pi / 180
    lat1, lon1 = latgrid * pifac, longrid * pifac
    lat2, lon2 = tclat * pifac, tclon * pifac
    dlat, dlon = lat1 - lat2, lon1 - lon2

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    r = EARTH_RADIUS_KM * 2 * np.arcsin(np.sqrt(np.minimum(1, a)))

    # ---- Rainfall rate ----
    rainfall = np.zeros_like(r)

    inside = r <= rm
    rainfall[inside] = T0 + (Tm - T0) * r[inside] / rm

    outside = (r > rm) & (r <= 800)
    rainfall[outside] = Tm * np.exp(-(r[outside] - rm) / re)

    # r > 800 km stays 0 (R-CLIPER truncation)
    return rainfall
