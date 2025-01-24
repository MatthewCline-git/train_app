import logging
import sys

# Basic logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("mta_api.log")],
)


# Create a logger
def get_logger(name: str = __name__):
    return logging.getLogger(name)
