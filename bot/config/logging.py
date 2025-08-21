import logging

def setup_logging(level: int = logging.INFO) -> None:
    """Configure basic logging for the project.

    Parameters
    ----------
    level: int, optional
        Logging level passed to ``logging.basicConfig``. By default
        :data:`logging.INFO` is used.
    """
    logging.basicConfig(level=level,
                        format="%(asctime)s - %(levelname)s - %(message)s")
