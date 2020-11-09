import os
import logging
from logging import FileHandler

plugin_root = os.path.dirname(os.path.realpath(__file__))
log_folder = os.path.join(plugin_root, 'logs')
# Logging format
screen_fmt = logging.Formatter(
    '%(asctime)s:%(levelname)s:%(module)s(%(lineno)d) - %(message)s')

goc_themes_id = '88f5c7a2-7b25-4ce8-a0c6-081236f5da76'
species_codes_id = 'cdc22563-dc61-4abc-9b6d-a863382e4b6c'

# hubapi_venv = os.environ.get('HUBAPI_VENV_CKAN')
hubapi_venv = '/home/dfo/.virtualenvs/hubapi/bin/python3'
hubapi_backup_script = '/home/dfo/hub-geo-api/backups.py'


def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # sh = logging.StreamHandler()
    # sh.setFormatter(screen_fmt)
    # sh.setLevel(level)
    # Only use file handler, don't fill up main CKAN log
    fh, log_file = get_file_logger()
    fh.setLevel(level)
    fh.setFormatter(screen_fmt)
    # if not logger.handlers:
    # logger.addHandler(sh)
    logger.addHandler(fh)
    logger.info('%s: Logging to %s' % (name, log_file))
    return logger


def get_file_logger():

    log_file = os.path.join(log_folder, 'dfoext.log')

    # Use rotating file handler, daily at midnight.
    # fh = TimedRotatingFileHandler(
    #     log_file,
    #     when='midnight',
    #     backupCount=30,
    #     encoding='utf-8')
    fh = FileHandler(log_file)
    fh.setFormatter(screen_fmt)
    return fh, log_file
