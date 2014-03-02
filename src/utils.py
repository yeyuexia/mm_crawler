import logging

LOG_FORMAT = "%(asctime)-15s -- %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger("crawler")

def info_log(message):
    logger.info(message)

def error_log(message):
    logger.error(message)

