"""Define elements to be used by a plugin and define the plugin API."""
from abc import ABC, abstractmethod
from typing import Any
from studio.session import SessionManager
from textual.dom import Widget


class Plugin(ABC):
    """
    A new instance of this plugin is created for each session.
    Each plugin must implement the following methods:
    """

    @abstractmethod
    def __init__(self, session: SessionManager) -> None:
        pass

    @abstractmethod
    def panel(self) -> Widget | None:
        """Returns the widget to be displayed in the panel for this plugin."""
        return None

    @abstractmethod
    def controls(self) -> dict[str, Any] | None:
        """Returns the controls (in renderable format) for modifying this plugin's behavior."""
        return None
