"""The model side of the MVC paradigm

# TODO:
- Clean up the way the Model part of the MVC is designed.
- Connect it up to the View/Controller.
"""
from typing import Optional, Any
from lang import FlowLangBase, FlowLang  # in the implementation
from abc import ABC, abstractmethod
from textual.widgets import TabPane, Collapsible
from textual.app import App as TextualApp
from core.signals import Signal
from pathlib import Path
from copy import deepcopy


class Flow:
    """
    Represents
    """
    def __init__(self):
        self.flow: FlowLangBase = FlowLang()
        self.src: str = ""

        # metadata
        self.name: str = ""
        self.file_path: Path = Path()
        self.is_dirty: bool = False

    def save_file(self):
        pass

    def open_file(self):
        pass


class Model:
    """
    The source of truth for the application state (a Singleton Pattern).
    Manages the current workspace and open file flows.
    """
    on_load: Signal = Signal()
    on_save: Signal = Signal()

    def __init__(self) -> None:
        self.project_name: str = ""  # name the user has given the project
        self.project_path: Optional[Path] = None

        # Active Flows
        self.flows: list[Flow] = []
        self.active_flow: Optional[Flow] = None

        # add default
        self.flows.append(_:=Flow())
        _.name = "Root"
        self.active_flow = _

    def get_flow_options(self) -> list[str]:
        """
        Returns list of tuples formatted for a Textual Select widget.
        """
        return [f.name for f in self.flows]

    def create_new_flow(self, name: str, branch_from_current: bool) -> bool:
        """Create a new Flow object and return True if the flow was created, otherwise False."""
        if name in (f.name for f in self.flows):
            return False
        self.flows.append(_:=(
            deepcopy(self.active_flow) if self.active_flow and branch_from_current else Flow()
        ))
        _.name = name
        self.active_flow = _
        return True

    def delete_selected_flow(self) -> None:
        new_flow_idx: int = self.flows.index(self.active_flow) - 1
        self.flows.remove(self.active_flow)
        if len(self.flows) > 0:
            self.active_flow = self.flows[new_flow_idx]
        else:
            self.active_flow = None

    # ==== Persistence ====
    def save(self, to_file: str) -> None:
        pass  # TODO implement

    @classmethod
    def load(cls, from_file: str) -> Model:
        pass  # TODO implement


# ================ Client Implemented  ================
class Plugin(ABC):
    """
    Any class that inherits from this, becomes a plugin and is expected to implement the methods below.
    Only one instance of this class is expected for each plugin PER APP.
    If session/flow-instance-specific behavior is desired, the session change signal must be watched and handled.

    Required attributes:
    - name: the name of the plugin
    """

    @abstractmethod
    def __init__(self, model: Model, app: TextualApp) -> None:
        pass

    @abstractmethod
    def panel(self) -> TabPane | None:
        """Returns the widget to be displayed in the panel for this plugin."""
        return None

    @abstractmethod
    def controls(self) -> tuple[str, list[Collapsible]] | None:
        """Returns the controls (in renderable format) for modifying this plugin's behavior."""
        return None

    def save_configuration(self):
        """Optional method to implement that is called by the editor when exiting."""
        pass
