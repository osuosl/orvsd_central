import logging
import os
from yaml import load

# Import environment variables
from .config_env import *

# path to yaml config
yaml_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'config.yml'
)))

# try to open that path, log an error if a problem occurs
try:
    yml_file = open(yaml_path, 'r')
except IOError, e:
    logging.error("Error reading yaml config: %s" % e)

# Load the yaml config
yaml_config = load(yml)

# Merge globals with the new yaml config
globals().update(yaml_config)
