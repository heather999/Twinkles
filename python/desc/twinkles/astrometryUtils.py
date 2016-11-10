import numpy as np
import numbers
from lsst.sims.utils import cartesianFromSpherical, sphericalFromCartesian
from lsst.sims.utils import rotationMatrixFromVectors
from lsst.sims.utils import _observedFromICRS, icrsFromObserved

__all__ = ["_rePrecess", "icrsFromPhoSim"]

def _rePrecess(ra_list, dec_list, obs):
    """
    Undo the 'dePrecession' done to mangle observed RA, Dec into the
    RA, Dec coordinates expected by PhoSim

    Parameters
    ----------
    ra_list a list of dePrecessed RA (in 'observed' frame)  in radians

    dec_list is a list of dePrecessed Dec (in 'observed' frame) in radians.

    *see lsst.sims.utils.AstrometryUtils.observedFromICRS for definition
    of 'observed' RA, Dec

    obs is an ObservationMetaData characterizing the telescope pointing

    Returns
    -------
    RA and Dec in 'observed' frame in radians
    """

    xyz_bore = cartesianFromSpherical(np.array([obs._pointingRA]),
                                      np.array([obs._pointingDec]))

    precessedRA, precessedDec = _observedFromICRS(np.array([obs._pointingRA]),
                                                  np.array([obs._pointingDec]),
                                                  obs_metadata=obs,
                                                  epoch=2000.0,
                                                  includeRefraction=False)

    xyz_precessed = cartesianFromSpherical(precessedRA, precessedDec)

    rotMat = rotationMatrixFromVectors(xyz_bore[0], xyz_precessed[0])

    xyz_list = cartesianFromSpherical(ra_list, dec_list)

    if isinstance(ra_list, numbers.Number):
        xyz_re_precessed = np.dot(rotMat, xyz_list)
    else:
        xyz_re_precessed = np.array([np.dot(rotMat, xx) for xx in xyz_list])

    ra_re_precessed, dec_re_precessed = sphericalFromCartesian(xyz_re_precessed)

    return ra_re_precessed, dec_re_precessed


def icrsFromPhoSim(ra_list, dec_list, obs):
    """
    Parameters
    ----------
    ra_list is the PhoSim ra value in degrees

    dec_list is the PhoSim dec value in degrees

    obs is the ObservationMetaData characterizing the pointing

    Returns
    -------
    RA, Dec in ICRS in degrees
    """

    ra_precessed, dec_precessed = _rePrecess(np.radians(ra_list),
                                             np.radians(dec_list),
                                             obs)

    return icrsFromObserved(np.degrees(ra_precessed), np.degrees(dec_precessed),
                            obs_metadata=obs, epoch=2000.0,
                            includeRefraction=False)