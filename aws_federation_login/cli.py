import argparse
import logging
import os
import sys
from dataclasses import dataclass

from aws_federation_login import LOGGER_NAME, federation_url


@dataclass
class CliArguments:
    destination_url: str
    duration: int
    debug: bool


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
parser.add_argument("--destination-url", type=str, help="The url navigate to after login")
parser.add_argument("--duration", type=int, help="Session duration in seconds")
args: CliArguments = parser.parse_args()  # type: ignore

loglevel = logging.DEBUG if args.debug else logging.WARNING
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(loglevel)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))
logger.addHandler(handler)


def main():
    try:
        sys.exit(federation_url.main(destination=args.destination_url, duration=args.duration))
    except EOFError:
        # Keyborardで Ctrl+C を入力されたとき (PyInquirerはEOFErrorを出す)
        sys.exit(1)
