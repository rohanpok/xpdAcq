import os
import socket
import yaml
import numpy as np
from unittest.mock import MagicMock
from time import strftime, sleep

from bluesky import RunEngine
from bluesky.utils import normalize_subs_input
from bluesky.callbacks import LiveTable
import bluesky.examples as be

# define simulated PE1C
class SimulatedPE1C(be.Reader):
    "Subclass the bluesky plain detector examples ('Reader'); add attributes."
    def __init__(self, name, fields):
        self.images_per_set = MagicMock()
        self.images_per_set.get = MagicMock(return_value=5)
        self.number_of_sets = MagicMock()
        self.number_of_sets.put = MagicMock(return_value=1)
        self.number_of_sets.get = MagicMock(return_value=1)
        self.cam = MagicMock()
        self.cam.acquire_time = MagicMock()
        self.cam.acquire_time.put = MagicMock(return_value=0.1)
        self.cam.acquire_time.get = MagicMock(return_value=0.1)

        super().__init__(name, fields)

        self.ready = True  # work around a hack in Reader


def setup_module():
    glbl.pe1c = SimulatedPE1C('pe1c', ['pe1c'])
    glbl.shutter = motor  # this passes as a fake shutter
    glbl.frame_acq_time = 0.1
    glbl._dark_dict_list = []


# better to get this from a config file in the fullness of time
HOME_DIR_NAME = 'xpdUser'
BLCONFIG_DIR_NAME = 'xpdConfig'
BEAMLINE_HOST_NAME = 'xf28id1-ws2'
ARCHIVE_BASE_DIR_NAME = 'pe2_data/.userBeamtimeArchive'
USER_BACKUP_DIR_NAME = strftime('%Y')
DARK_WINDOW = 3000 # default value, in terms of minute
FRAME_ACQUIRE_TIME = 0.1 # pe1 frame acq time
OWNER = 'xf28id1'
BEAMLINE_ID = 'xpd'
GROUP = 'XPD'


# change this to be handled by an environment variable later
hostname = socket.gethostname()
if hostname == BEAMLINE_HOST_NAME:
    simulation = False
else:
    simulation = True

if simulation:
    BASE_DIR = os.getcwd()
else:
    BASE_DIR = os.path.expanduser('~/')

# top directories
HOME_DIR = os.path.join(BASE_DIR, HOME_DIR_NAME)
BLCONFIG_DIR = os.path.join(BASE_DIR, BLCONFIG_DIR_NAME)
ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,ARCHIVE_BASE_DIR_NAME)

# aquire object directories
CONFIG_BASE = os.path.join(HOME_DIR, 'config_base')
YAML_DIR = os.path.join(HOME_DIR, 'config_base', 'yml')
""" Expect dir
config_base/
            yaml/
                bt_bt.yaml
                samples/
                experiments/
                scanplnas/
"""
BT_DIR = YAML_DIR
SAMPLE_DIR  = os.path.join(YAML_DIR, 'samples')
EXPERIMENT_DIR  = os.path.join(YAML_DIR, 'experiments')
SCANPLAN_DIR  = os.path.join(YAML_DIR, 'scanplans')
# other dirs
IMPORT_DIR = os.path.join(HOME_DIR, 'Import')
ANALYSIS_DIR = os.path.join(HOME_DIR, 'userAnalysis')
USERSCRIPT_DIR = os.path.join(HOME_DIR, 'userScripts')
TIFF_BASE = os.path.join(HOME_DIR, 'tiff_base')
USER_BACKUP_DIR = os.path.join(ARCHIVE_BASE_DIR, USER_BACKUP_DIR_NAME)

ALL_FOLDERS = [
        HOME_DIR,
        BLCONFIG_DIR,
        YAML_DIR,
        CONFIG_BASE,
        SAMPLE_DIR,
        EXPERIMENT_DIR,
        SCANPLAN_DIR,
        TIFF_BASE,
        USERSCRIPT_DIR,
        IMPORT_DIR,
        ANALYSIS_DIR
        ]

# directories that won't be tar in the end of beamtime
_EXCLUDE_DIR = [HOME_DIR, BLCONFIG_DIR, YAML_DIR]
_EXPORT_TAR_DIR = [CONFIG_BASE, USERSCRIPT_DIR]

# for simulation put a dummy bt object in xpdUser/config_base/yml/
os.makedirs(BLCONFIG_DIR, exist_ok=True)
tmp_safname = os.path.join(BLCONFIG_DIR,'saf123.yml')
if not os.path.isfile(tmp_safname):
    dummy_config = {'saf number':123,'PI last name':'simulation','experimenter list':[('PIlastname','PIfirstname',1123456),('Exp2lastname','Exp2firstname',654321),
                     ('Add more lines','as needed, one for each experimenter',98765)]}
    with open(tmp_safname, 'w') as fo:
        yaml.dump(dummy_config,fo)

class glbl():
    beamline_host_name = BEAMLINE_HOST_NAME
    base = BASE_DIR
    home = HOME_DIR
    _export_tar_dir = _EXPORT_TAR_DIR
    xpdconfig = BLCONFIG_DIR
    import_dir = IMPORT_DIR
    config_base = CONFIG_BASE
    tiff_base =TIFF_BASE
    usrScript_dir = USERSCRIPT_DIR
    yaml_dir = YAML_DIR
    bt_dir = BT_DIR
    sample_dir = SAMPLE_DIR
    experiment_dir = EXPERIMENT_DIR
    scanplan_dir = SCANPLAN_DIR
    allfolders = ALL_FOLDERS
    archive_dir = USER_BACKUP_DIR
    dk_window = DARK_WINDOW
    frame_acq_time = FRAME_ACQUIRE_TIME
    auto_dark = True
    owner = OWNER
    beamline_id = BEAMLINE_ID
    group = GROUP
    _dark_dict_list = [] # initiate a new one every time

    # logic to assign correct objects depends on simulation or real experiment
    if not simulation:
        from bluesky.run_engine import RunEngine
        from bluesky.register_mds import register_mds
        # import real object as other names to avoid possible self-referencing later
        from bluesky import Msg as msg
        from bluesky.plans import Count as count
        from bluesky.plans import AbsScanPlan as absScanPlan
        from databroker import DataBroker
        from databroker import get_images as getImages
        from databroker import get_events as getEvents
        from bluesky.callbacks import LiveTable as livetable
        from bluesky.callbacks.broker import verify_files_saved as verifyFiles
        from ophyd import EpicsSignalRO, EpicsSignal
        from bluesky.suspenders import SuspendFloor
        ring_current = EpicsSignalRO('SR:OPS-BI{DCCT:1}I:Real-I', name='ring_current')
        xpdRE = RunEngine()
        xpdRE.md['owner'] = owner
        xpdRE.md['beamline_id'] = beamline_id
        xpdRE.md['group'] = group
        register_mds(xpdRE)
        beamdump_sus = SuspendFloor(ring_current, ring_current.get()*0.9,
                resume_thresh = ring_current.get()*0.9, sleep = 1200)
        #xpdRE.install_suspender(beamdump_sus) # don't enable it untill beam is back
        # real imports
        Msg = msg
        Count = count
        db = DataBroker
        LiveTable = livetable
        get_events = getEvents
        get_images = getImages
        AbsScanPlan = absScanPlan 
        verify_files_saved = verifyFiles
        # real collection objects will be loaded during start_up
        area_det = None
        temp_controller = None
        shutter = None
        
    else:
        simulation = True
        
        # shutter = motor  # this passes as a fake shutter
        frame_acq_time = 0.1
        ARCHIVE_BASE_DIR = os.path.join(BASE_DIR,'userSimulationArchive')
        # mock imports
        Msg = MagicMock()
        Count = MagicMock()
        AbsScanPlan = MagicMock()
        db = MagicMock()
        get_events = MagicMock()
        get_images = MagicMock()
        LiveTable = None # FIXME real import later
        verify_files_saved = MagicMock()
        # mock collection objects
        area_det = SimulatedPE1C('pe1c', ['pe1c'])
        temp_controller = be.motor
        shutter = MagicMock()
        print('==== Simulation being created in current directory:{} ===='.format(BASE_DIR))
