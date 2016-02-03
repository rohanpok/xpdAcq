#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
## testing section ##
from bluesky.plans import Count # fake object but exact syntax
#####################

import numpy as np
import matplotlib.pyplot as plt

from xpdacq.control import _get_obj

from dataportal import DataBroker as db

print('Before you start, make sure the area detector IOC is in "Continuous mode"')
#expo_threshold = 60 # in seconds Deprecated!
ACQUIRE_TIME = 0.1 # default frame rate
AREA_DET_NAME = 'pe1c'


# set up the detector    
# default settings for pe1c
area_det = _get_obj(AREA_DET_NAME)
area_det.cam.acquire_time.put(ACQUIRE_TIME)


################# private module ###########################
def _bluesky_global_state():
    '''Import and return the global state from bluesky.'''

    from bluesky.standard_config import gs
    return gs

def _bluesky_metadata_store():
    '''Return the dictionary of bluesky global metadata.'''

    gs = _bluesky_global_state()
    return gs.RE.md

def _bluesky_RE():
    import bluesky
    from bluesky.run_engine import RunEngine
    from bluesky.register_mds import register_mds
    #from bluesky.run_engine import DocumentNames
    RE = RunEngine()
    register_mds(RE)
    return RE

RE = _bluesky_RE()

RE.md_validator = ensure_sc_uid

##############################################################
def ensure_sc_uid(md):
    if 'sc_uid' not in md:
        raise ValueError("scan metadata needed to run scan.  Please create a scan metadata object and rerun.")


def get_light_images(mdo, exposure = 1.0, area_det=area_det):
    '''the main xpdAcq function for getting an exposure
    
    Right now it assumes continuous acquisition mode for the detector.
    
    Arguments:
      mdo - xpdacq.beamtime.Scan metadata object - generated by beamtime metadata setup sequence
      area_det - bluesky detector object - the instance of the detector you are using. 
                   by default area_det defined when xpdacq is loaded
      exposure - float - exposure time in seconds

    Returns:
      nothing
    '''   
    from bluesky.plans import Count
    from xpdanl.xpdanl import plot_last_one
    from xpdacq.beamtime import Xposure

    exp = Xposure(mdo)

    # compute number of frames and save metadata
    num_frame = int(exposure / area_det.cam.acquire_time)
    if num_frame == 0: num_frame = 1
    computed_exposure = num_frame*area_det.cam.acquire_time
    print('INFO: requested exposure time = ',exposure,' -> computed exposure time:',computed_exposure)
    exp.md.update({'xp_requested_exposure':exposure,'xp_computed_exposure':computed_exposure}) 
    exp.md.update({'xp_time_per_frame':area_det.cam.acquire_time,'xp_num_frames':num_frame})
    
#    area_det.image_per_set.put(num_frame)
    md_dict = exp.md
    if not validate_md(md_dict):
        raise ValueError("blah blah")

    
    plan = Count([area_det], num= num_frame)
    gs.RE(plan,**md_dict)
        
    print('End of get_light_image...')

def _xpd_plan_1(num_saturation, num_unsaturation, det=None):
    ''' type-1 plan: change image_per_set on the fly with Count
    
    Parameters:
    -----------
        num_img : int
            num of images you gonna take, last one is fractional
        
        time_dec : flot
    '''
    from bluesky import Msg
    from xpdacq.control import _get_obj
    
    if not det:
        _det = _get_obj('pe1c')

    num_threshold = int(expo_threshold / frame_rate)

    yield Msg('open_run')
    yield Msg('stage', _det)
    _det.number_of_sets.put(1)
    
    _det.image_per_set.put(num_threshold)
    for i in range(num_saturation):
        yield Msg('create')
        yield Msg('trigger', _det)
        yield Msg('read', _det)
        yield Msg('save')
    
    _det.image_per_set.put(num_unsaturation)
    yield Msg('create')
    yield Msg('trigger', _det)
    yield Msg('read', _det)
    yield Msg('save')
    yield Msg('close_run')


    # reproduce QXRD workflow. Do dark and light scan with the same amount of time so that we can subtract it
    # can be modified if we have better understanding on dark current on area detector    
    
    def QXRD_plan():
        print('Collecting dark frames....')
        _close_shutter()
        yield from count_plan
        print('Collecting light frames....')
        _open_shutter()
        yield from count_plan

    RE(QXRD_plan())
    
        
    # hook to visualize data
    # FIXME - make sure to plot dark corrected image
    plot_scan(db[-1])


