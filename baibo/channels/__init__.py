"""Chat channels module with plugin architecture."""

from baibo.channels.base import BaseChannel
from baibo.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
