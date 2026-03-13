# Textual Imports
from textual.widgets import Collapsible, TabPane, Input, Checkbox, Button, ProgressBar, Label, RichLog
from textual.widget import Widget
from textual.containers import ScrollableContainer

# Standard Imports
from typing import Iterator
import time
import psutil
import os
from studio.model import Plugin


class P(Plugin):
    def on_initialized(self) -> None:
        self.name = 'run'

        # Connect the Test button to our execution logic
        self.view.sig_button_pressed.connect(
            lambda e: self.execute_run() if e.button.id == 'btn-run' else None
        )

    def controls(self) -> Iterator[Widget]:
        # NOTE: there aren't that many settings for the run tab due to most controls being available through the DSL.

        with Collapsible(title='Hot Reload', collapsed=False):
            self.hot_mode = Checkbox('Enable Hot Reload Mode')
            yield self.hot_mode
            self.hot_n_changes = Input(type='integer', value='1')
            self.hot_n_changes.border_title = 'Re-run after N changes'
            yield self.hot_n_changes
            self.hot_timeout = Input(type='number', value='500')
            self.hot_timeout.border_title = 'Timeout (ms)'
            yield self.hot_timeout

        with Collapsible(title='Profiler', collapsed=False):
            self.enable_progress_bar = Checkbox('Progress bar', value=True)
            yield self.enable_progress_bar
            self.enable_program_stats = Checkbox('Resource usage stats', value=True)
            yield self.enable_program_stats

    def panel(self) -> TabPane | None:
        # 1. Progress Bar Widget
        self.progress_bar = ProgressBar(total=100, show_eta=True, id="run-progress-bar")
        self.progress_container = Collapsible(self.progress_bar, title="Execution Progress", collapsed=False)

        # 2. Run Stats Widget (Mem usage & Time)
        self.stats_label = Label("Waiting for run...", id="run-stats-label")
        self.stats_container = Collapsible(self.stats_label, title="Profiler Stats", collapsed=False)

        # 3. Errors & Parser Notes Widget
        self.log_view = RichLog(id="run-log-view", highlight=True, markup=True, wrap=True)
        clear_log = Button('Clear Log', id="clear-log")
        self.log_container = Collapsible(self.log_view, clear_log, title="Errors & Parser Notes", collapsed=False)

        return TabPane(
            self.name.title(),
            ScrollableContainer(
                self.progress_container,
                self.stats_container,
                self.log_container
            )
        )

    def execute_run(self) -> None:
        """Handles the flow execution and updates the UI components."""

        # Toggle visibility based on user settings in controls()
        self.progress_container.display = self.enable_progress_bar.value
        self.stats_container.display = self.enable_program_stats.value

        active_flow_session = self.model.active_flow
        if not active_flow_session:
            self.log_view.write("[bold red]Error:[/bold red] No active flow selected to run.")
            return

        self.log_view.write(f"[bold green]Starting run for '{active_flow_session.name}'...[/bold green]")

        # Memory and Time profiling setup (referenced from interpreter.py)
        process = psutil.Process(os.getpid())
        mem_start = process.memory_info().rss / 1024 / 1024
        start_time = time.perf_counter()

        try:
            self.model.active_flow.flow.interpret(self.view.code_editor_text_area.text)

            # If the progress bar is enabled, advance it:
            if self.enable_progress_bar.value:
                self.progress_bar.advance(100)  # Mock completion

        except Exception as e:
            self.log_view.write(f"[bold red]Execution Error:[/bold red] {str(e)}")

        finally:
            # Calculate and display stats
            if self.enable_program_stats.value:
                mem_end = process.memory_info().rss / 1024 / 1024
                elapsed_time = time.perf_counter() - start_time
                mem_diff = mem_end - mem_start
                self.stats_label.update(
                    f"[bold]Time Spent:[/bold] {elapsed_time:.4f} seconds\n"
                    f"[bold]Memory Change:[/bold] {mem_diff:+.2f} MB\n"
                    f"[bold]Total Memory:[/bold] {mem_end:.2f} MB"
                )
plugin = P()
