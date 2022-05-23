import argparse
import logging
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from os import path

from jinja2 import Environment, FileSystemLoader

from aws_federation_login import LOGGER_NAME, federation_url


@dataclass
class CliArguments:
    destination_url: str
    duration: int
    debug: bool = False
    web: bool = False


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
parser.add_argument("--destination-url", type=str, help="The url navigate to after login")
parser.add_argument("--duration", type=int, help="Session duration in seconds")
parser.add_argument("--web", action="store_true", help="open your browser and show the url in it")
args: CliArguments = parser.parse_args()  # type: ignore

loglevel = logging.DEBUG if args.debug else logging.WARNING
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(loglevel)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))
logger.addHandler(handler)


def open_link_page(
    url: str, destination: str, template_dir: str, temphtml: tempfile._TemporaryFileWrapper
):
    env = Environment(
        loader=FileSystemLoader(template_dir),
    )
    template = env.get_template("signin.template.html")
    params = {
        "url": url,
        "destination": destination,
    }
    temphtml.write(template.render(params))
    webbrowser.open(f"file://{temphtml.name}")


def main():
    try:
        destination = args.destination_url
        duration = args.duration

        federation_login = federation_url.main(destination=destination, duration=duration)
        # output_path = path.join(app_build_path(), "signin.html")
        template_dir = path.join(path.dirname(__file__), "assets")
        logger.debug(f"{template_dir=}")

        if args.web:
            with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as temphtml:
                open_link_page(
                    url=federation_login.url,
                    destination=federation_login.destination,
                    template_dir=template_dir,
                    temphtml=temphtml,
                )
        else:
            print(federation_login.url)

        sys.exit(0)
    except EOFError:
        # Keyborardで Ctrl+C を入力されたとき (PyInquirerはEOFErrorを出す)
        sys.exit(1)
