import sys
from loguru import logger

def setup_logger():
    """
    Configures a standardized logger for the CHS-SDK.
    """
    logger.remove()  # Remove default handler to avoid duplicate outputs
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    # Example of adding a file logger (optional, can be configured via a config file)
    # logger.add(
    #     "logs/chs_sdk_{time}.log",
    #     level="DEBUG",
    #     rotation="10 MB",
    #     retention="10 days",
    #     format="{time} {level} {message}",
    #     enqueue=True,  # Make it process-safe
    #     backtrace=True,
    #     diagnose=True,
    # )
    return logger

# Create a globally accessible logger instance
log = setup_logger()
