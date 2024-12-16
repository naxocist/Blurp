import logging
from logging.config import dictConfig

# logging.basicConfig(level=logging.DEBUG, filename='log.log', filemode='w', 
#                     format="%(asctime)s | %(filename)s - %(levelname)s - %(message)s")

config = {
  'version': 1,
  'disable_existing_logger': False,
  'Loggers': {
    "": {
        'level': "DEBUG"
    }
  }
}

dictConfig(config)

logging.debug("debug")
logging.info("info")
logging.warning("warning")
logging.error("error")
logging.critical("critical")
