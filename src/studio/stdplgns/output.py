# Textual Imports
from textual.widgets import Collapsible, TabPane, Input, Checkbox, Label, DataTable, SelectionList, Button
from rich.text import Text
from textual.widgets.data_table import CellKey
from textual.widget import Widget
from textual.coordinate import Coordinate
from textual.widgets.selection_list import Selection

# Standard Imports
from typing import Iterator
from studio.model import Plugin, FlowLang, FlowLangBase


class P(Plugin):
    def on_initialized(self) -> None:
        self.name = 'output'

        # connect model signals
        self.model.active_flow.flow.on_evolved_n.connect(self.on_evolved)
        self.model.active_flow.flow.on_undone_n.connect(self.on_undo)
        self.model.active_flow.flow.on_clear.connect(self.on_clear)

        # connect view signals
        self.view.sig_checkbox_changed.connect(self.handle_checkbox)

    def controls(self) -> Iterator[Widget]:
        with Collapsible(title='Column Controls', collapsed=False):
            self.hidden_space_columns = Input()
            self.hidden_space_columns.border_title = 'Hidden spaces'
            yield self.hidden_space_columns
            self.column_controls = SelectionList(
                Selection("Event indices", 0, True),
                Selection("Causal distance", 1, True),
                Selection("Causally connected", 2, True),
                Selection(" ├─ Collapsed", 3, False),
                Selection(" ╰─ Counted", 4, False)
            )
            yield self.column_controls

        with Collapsible(title='Pattern Queries', collapsed=False):
            self.search_pattern = Input()
            self.search_pattern.border_title = 'Search pattern'
            yield self.search_pattern
            self.created_at = Input()
            self.created_at.border_title = 'Created at event(s)'
            yield self.created_at
            self.destroyed_at = Input()
            self.destroyed_at.border_title = 'Destroyed at event(s)'
            yield self.destroyed_at
            yield Button('Find', id="find-pattern-filters")

        with Collapsible(title='Selection Info', collapsed=False):
            self.selection_info_label = Label('Event Info:\n- Cells: 0\n- Connected: 0\n')
            yield self.selection_info_label
            self.selection_info_label = Label('Cell Info:\n- created at: None\n- destroyed at: None\n')
            yield self.selection_info_label
            self.hover_explorer = Checkbox('Hover explorer')
            yield self.hover_explorer

        yield Label()

    def handle_checkbox(self, sig: Checkbox.Changed) -> None:
        pass

    def panel(self) -> TabPane | None:
        self.data_table = DataTable(id='data-table')
        self.data_table.add_columns('Time')
        self.data_table.add_columns('Distance')
        self.data_table.add_columns('Connected')
        self.data_table.add_columns('Evolution')
        return TabPane(
            self.name.title(),
            self.data_table
        )

    def on_evolved(self, f: FlowLangBase, steps: int) -> None:
        cft = self.cft
        if self.data_table.row_count == 0:
            steps += 1  # to include the first space state
        for event in f.events[-steps:]:
            cft(  # we are potentially calling from thread, thus this.
                self.data_table.add_row,
                event.time,
                event.causal_distance_to_creation,
                tuple(event.causally_connected_events),
                str(event.spaces.__next__())
                .replace('A', '[on blue3] A [/on blue3]')
                .replace('B', '[on magenta] B [/on magenta]')
                .replace('C', '[on yellow] C [/on yellow]')
            )

    def on_undo(self, f: FlowLangBase, steps: int) -> None:
        cft = self.cft
        if (_:=self.data_table.row_count) < steps:
            steps = _
        for _ in range(steps):
            cell_key: CellKey = self.data_table.coordinate_to_cell_key(
                Coordinate(self.data_table.row_count - 1, 0)
            )
            cft(self.data_table.remove_row, cell_key.row_key)

    def on_clear(self):
        self.data_table.clear()

plugin = P()
