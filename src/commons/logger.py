import logging
import sys


def setup_logging(level=logging.INFO) -> None:
    root = logging.getLogger()
    root.handlers.clear()  # reset existing handlers (important in notebooks)
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    root.addHandler(handler)


setup_logging(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info("logging is ready")
