"""Define elements to be used by a plugin and define the plugin API."""
from src.lang import FlowLangBase as FlowL, FlowLang  # in the implementation
from textual.app import App


class SessionManager:
    """This is the main session class (meant to be used as a Singleton) that stores all current sessions."""

    def __init__(self, parent_app: App) -> None:
        # Flow Classes
        self.flow_classes: dict[str, type[FlowL]] = {
            'FlowLang': FlowLang
        }
        self.selected_flow_class: str = 'FlowLang'

        # Active Sessions
        self.sessions: dict[str, FlowL] = {}  # Flow instances
        self.selected_session: str = 'Default'

        # ====== Parent Reference (so that plugin classes can access all aspects of parents) ======
        self.app: App = parent_app

    # ==== Session ====
    @property
    def current_session(self) -> FlowL:
        return self.sessions[self.selected_session]

    def set_selected_session(self, name: str) -> None:
        self.selected_session = name

    def create_new_session(self, name: str) -> None:
        self.sessions[name] = self.current_flow_class()
        self.set_selected_session(name)

    # ==== Flow Class ====
    @property
    def current_flow_class(self) -> type[FlowL]:
        return self.flow_classes[self.selected_flow_class]

    def set_selected_flow_class(self, name: str) -> None:
        self.selected_flow_class = name

    def register_flow_class(self, flow_class: type[FlowL]) -> None:
        self.flow_classes[flow_class.__name__] = flow_class

    # ==== Persistence ====
    def save(self, to_file: str) -> None:
        pass  # TODO implement

    @classmethod
    def load(cls, from_file: str) -> SessionManager:
        pass  # TODO implement
