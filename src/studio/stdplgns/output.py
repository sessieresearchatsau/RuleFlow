# Textual Imports
from textual.widgets import Collapsible, TabPane, Input, Checkbox, Label, DataTable
from textual.widgets.data_table import CellKey
from textual.widget import Widget
from textual.coordinate import Coordinate
from textual.containers import ScrollableContainer

# Standard Imports
from typing import Iterator
from studio.model import Plugin, FlowLang


class P(Plugin):
    def on_initialized(self) -> None:
        self.name = 'output'

        # connect signals
        self.model.active_flow.flow.on_evolve.connect(self.on_evolved)
        self.model.active_flow.flow.on_undo.connect(self.on_undo)

    def controls(self) -> Iterator[Widget]:
        self.render_range = Input()
        self.render_range.border_title = 'Render Range'
        yield self.render_range
        self.live_step = Checkbox('Live Step')
        yield self.live_step

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

    def panel(self) -> TabPane | None:
        self.data_table = DataTable(id='data-table')
        self.data_table.add_columns('Steps')

        return TabPane(
            self.name.title(),
            self.data_table
        )

    def on_evolved(self):
        self.data_table.add_row(str(self.model.active_flow.flow.current_event.spaces.__next__()))
        self.data_table.scroll_end(x_axis=False, animate=False)

    def on_undo(self):
        cell_key: CellKey = self.data_table.coordinate_to_cell_key(Coordinate(self.data_table.row_count - 1, 0))
        self.data_table.remove_row(cell_key.row_key)
        self.data_table.scroll_end(x_axis=False, animate=False)

plugin = P()
