"""Tool registration imports — imported by server.py for side-effect registration."""

from .diary import register_diary_tool

__all__ = ["register_diary_tool"]
