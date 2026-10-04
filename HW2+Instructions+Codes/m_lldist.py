"""Spherical-earth distance between lon/lat points (Python port of m_lldist_L)."""
import numpy as np

EARTH_RADIUS_KM = 6378.137


def m_lldist_L(lon, lat):
    """Distance between successive lon/lat points.

    Parameters
    ----------
    lon, lat : array-like, degrees (at least two values each)

    Returns
    -------
    dict with numpy arrays (length n-1), in km:
        dist : great-circle distance
        dx   : east-west component (signed by dlon)
        dy   : north-south component (signed by dlat)
    """
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)

    if lon.size < 2 or lat.size < 2:
        raise ValueError("lon and lat must each contain at least two values.")

    pifac = np.pi / 180
    lon1, lon2 = lon[:-1] * pifac, lon[1:] * pifac
    lat1, lat2 = lat[:-1] * pifac, lat[1:] * pifac
    dlon, dlat = lon2 - lon1, lat2 - lat1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    dist = EARTH_RADIUS_KM * 2 * np.arcsin(np.sqrt(np.minimum(1, a)))

    dx = (EARTH_RADIUS_KM * 2
          * np.arcsin(np.sqrt(np.maximum(0, np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2)))
          * np.sign(dlon))
    dy = (EARTH_RADIUS_KM * 2
          * np.arcsin(np.sqrt(np.minimum(1, np.sin(dlat / 2) ** 2)))
          * np.sign(dlat))

    return {"dist": dist, "dx": dx, "dy": dy}
