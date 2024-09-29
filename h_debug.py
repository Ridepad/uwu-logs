import logging
from time import perf_counter

from c_path import Directories

LOGGING_FORMAT_DEFAULT = '''%(asctime)s | %(levelname)-8s | %(filename)22s:%(lineno)-4s | %(message)s'''
LOGGING_FORMAT = {
    "connections" : '''%(asctime)s | %(message)s''',
}

def setup_logger(logger_name):
    log_file = Directories.loggers / f'{logger_name}.log'
    logger = logging.getLogger(logger_name)
    _format = LOGGING_FORMAT.get(logger_name, LOGGING_FORMAT_DEFAULT)
    formatter = logging.Formatter(_format)
    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

class Loggers(dict[str, logging.Logger]):
    __getattr__ = dict.get

    connections = setup_logger('connections')
    reports = setup_logger('reports')
    uploads = setup_logger('uploads')
    unusual_spells = setup_logger('unusual_spells')
    memory = setup_logger('memory')
    archives = setup_logger("archives")
    player_queue = setup_logger('player_queue')
    ladder_watchdog = setup_logger('ladder_watchdog')
    ladder_parser = setup_logger('ladder_parser')
    missing = setup_logger('missing')
    top = setup_logger('top')
    gear = setup_logger('gear')

    raging_gods = setup_logger("raging_gods")

def get_ms(timestamp):
    if timestamp is None:
        return -1
    return int((perf_counter()-timestamp)*1000)

def get_ms_str(timestamp):
    return f"{get_ms(timestamp):>7,} ms"

def running_time(f):
    _logger = Loggers.reports
    def running_time_inner(*args, **kwargs):
        timestamp = perf_counter()
        q = f(*args, **kwargs)
        msg = f"{get_ms_str(timestamp)} | {f.__module__}.{f.__name__}"
        _logger.debug(msg)
        return q
    
    return running_time_inner
