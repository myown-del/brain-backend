import logging
import sys


def _resolve_logging_level(logging_level: str | int) -> int:
    if isinstance(logging_level, int):
        return logging_level
    return logging._nameToLevel.get(str(logging_level).upper(), logging.INFO)


def setup_logging(logging_level: str | int = "INFO") -> None:
    logging.basicConfig(
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
        level=_resolve_logging_level(logging_level),
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
        format=("{asctime} [{levelname:.1}] [{name:^16}] {message}"),
    )
