import logging
import os
import sys

from aws_federation_login import LOGGER_NAME, federation_url

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(os.environ.get("LOGLEVEL", "DEBUG").upper())
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))
logger.addHandler(handler)


def main():
    try:
        sys.exit(federation_url.main())
    except EOFError:
        # Keyborardで Ctrl+C を入力されたとき (PyInquirerはEOFErrorを出す)
        sys.exit(1)
