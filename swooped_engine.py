"""Compatibility exports for the fast local browser-backed Swooped engine."""

from browser_engine import BrowserSwoopedEngine, DOWNLOADS_DIR, PREVIEWS_DIR

SwoopedEngine = BrowserSwoopedEngine

__all__ = ["SwoopedEngine", "BrowserSwoopedEngine", "DOWNLOADS_DIR", "PREVIEWS_DIR"]
