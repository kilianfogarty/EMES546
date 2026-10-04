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
    a1 = a2 = a3 = a4 = None
    b1 = b2 = b3 = b4 = None
    if None in (a1, a2, a3, a4, b1, b2, b3, b4):
        raise NotImplementedError("Fill in the R-CLIPER coefficients a1..a4, b1..b4.")

    # ---- Normalized intensity ----
    U = None  # FILL IN: normalized intensity as a function of Vmax
    if U is None:
        raise NotImplementedError("Fill in the equation for U.")

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
