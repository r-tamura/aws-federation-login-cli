import logging

LOGGER_NAME = "aws_federation_login"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
