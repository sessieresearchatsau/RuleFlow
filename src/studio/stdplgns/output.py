# Textual Imports
from textual.widgets import Collapsible, TabPane, Input, Checkbox, Button, Label
from textual.widget import Widget
from textual.containers import ScrollableContainer

# Standard Imports
from typing import Iterator
from studio.model import Plugin


class P(Plugin):
    def on_initialized(self) -> None:
        self.name = 'output'

    def panel(self) -> TabPane | None:
        return TabPane(self.name.title())

    def controls(self) -> Iterator[Widget]:
        self.live_update_mode = Checkbox('Live Update Mode')
        yield self.live_update_mode
        self.render_range = Input()
        self.render_range.border_title = 'Render Range'
        yield self.render_range

        with Collapsible(title='Pattern Queries', collapsed=False):
            self.search_pattern = Input()
            self.search_pattern.border_title = 'Search Pattern'
            yield self.search_pattern
            self.created_at = Input()
            self.created_at.border_title = 'Created at Event(s)'
            yield self.created_at
            self.destroyed_at = Input()
            self.destroyed_at.border_title = 'Destroyed at Event(s)'
            yield self.destroyed_at
            self.highlight_matches = Checkbox('Highlight all matching events')
            yield self.highlight_matches

        with Collapsible(title='Selection Info', collapsed=False):
            self.selection_info_label = Label('Selection Info:\n- created at: None\n- destroyed at: None')
            yield self.selection_info_label
            self.enable_hover_highlighting = Checkbox('Enable Hover Highlighting')
            yield self.enable_hover_highlighting

        with Collapsible(title='Column Controls', collapsed=True):
            self.show_event_indices = Checkbox('Show Event Indices')
            yield self.show_event_indices
            self.show_causally_connected = Checkbox('Show Causally connected')
            yield self.show_causally_connected

        with Collapsible(title='Branch Paths', collapsed=True):
            self.branch_render_range = Input()
            self.branch_render_range.border_title = 'Branch Range(s)'
            yield self.branch_render_range
            self.interactive_selection_mode = Checkbox('Interactive Mode')
            yield self.interactive_selection_mode
plugin = P()
