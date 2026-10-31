"""Compatibility exports for the fast local browser-backed Swooped engine."""

from browser_engine import (
    BrowserAutomationError,
    BrowserSwoopedEngine,
    DOWNLOADS_DIR,
    PREVIEWS_DIR,
    PipelineCancelled,
)

SwoopedEngine = BrowserSwoopedEngine

__all__ = [
    "SwoopedEngine",
    "BrowserSwoopedEngine",
    "BrowserAutomationError",
    "PipelineCancelled",
    "DOWNLOADS_DIR",
    "PREVIEWS_DIR",
]
