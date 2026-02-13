"""Configuration module for baibo."""

from baibo.config.loader import get_config_path, load_config
from baibo.config.schema import Config

__all__ = ["Config", "load_config", "get_config_path"]
