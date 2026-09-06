# Procedures to manually test RuleFlow

================ General UI & Project Management ================

*   Launch the application and verify the Welcome Screen renders correctly in the terminal.
*   Create a new project using the "New" button. 
*   Attempt to create a project without a name or path to verify that the error notifications trigger properly.
*   Attempt to create a project with a duplicate name to trigger the duplicate ID validation.
*   Open an existing project from the "Recent Projects" list.
*   Verify that the left sidebar contains the project directory tree and the top toolbar displays the active file.
*   Click and drag the vertical splitter separating the project directory from the workspace. Verify that the panel resizes smoothly between the minimum of 15 columns and maximum of 80 columns without highlighting text.
*   Click and drag the vertical splitter separating the workspace from the right-hand plugin controls.
*   Toggle the "+ " and "-" buttons in the project directory pane to create and remove temporary file variants. 
*   Verify that you cannot delete the "main" variant.
*   Attempt to exit the application using `ctrl+q` and verify that the exit confirmation modal appears.

================ Execute Plugin Testing ================

*   Open a valid `.flow` or `.pflow` file.
*   Navigate to the "Execute" tab in the right-hand panel.
*   Click the "Execute" button (green play button) in the top toolbar to run the script.
*   Verify that the "Execution Progress" bar updates accurately as the flow evolves.
*   Click the "Regress" button (orange) and verify the state undoes the specified number of steps.
*   Click the "Clear" button (red) to dump the flow memory. Check the Program Log to ensure it reports the memory clearance.
*   Expand the "Hot Reload" collapsible section.
*   Enable hot reload and set "After n changes" to a small integer like `3`. 
*   Type characters into the code editor and verify that the system automatically triggers a re-execution when the threshold is met.
*   Enable the "Show memory profile" checkbox and execute a script. 
*   Verify that the log output displays the "Memory Profile Report" detailing time spent, memory change, and total studio memory.

================ Explore Plugin Testing ================

*   Navigate to the "Explore" tab.
*   Expand the "Table Controls" collapsible menu.
*   Toggle various columns (e.g., Causal Distance, Created Cells, Space Count) in the Data Table SelectionList to verify they dynamically appear and disappear in the central workspace.
*   Move your mouse over the inner cells of the generated Data Table. 
*   Expand the "Hover Explorer" menu and enable "Show Cell Info". 
*   Verify that hovering over distinct cells updates the Cell Info panel with the correct Quanta, Generation, and Identity values.
*   Enable "Highlight Generation" and "Highlight Identity". Hover over cells to ensure the Textual styling (e.g., "on green" or "on yellow") applies instantly to matching cells across the table.
*   Expand the "Cell Rendering" menu. 
*   Modify the "Base Style", "Cell Width", and "Justify" inputs, then press Enter to submit. Verify that the table reformats according to the new CSS/Textual style rules.
*   Toggle the "Ordered Spectrum" checkbox and manually input a "Color Palette" seed to ensure deterministic color assignments shift correctly.
*   Change the "Encode Property" RadioSet from Quanta to Generation and verify the symbols update in the table.

================ Analysis Plugin Testing ================

*   Navigate to the "Analysis" tab.
*   Execute a flow script to generate event data.
*   Expand the "Causal Network" menu and type `:10` in the "Event Range" input, then click "Build Graph".
*   Check the bottom "Causal Network Metrics" data table to ensure calculations (like Edge-Node Ratio and Network Density) update accurately.
*   Select "GraphML" from the export dropdown and click "Export as Format". Verify that the file successfully saves to the project directory.
*   Expand the "VisJS Viewer" menu.
*   Toggle specific UI filters in the SelectionList (e.g., Nodes, Edges, Physics).
*   Click "View Graph" to generate the HTML export. Verify that the system attempts to open it in your default web browser.
*   Expand the "Causal Distribution" menu and click "Calculate".
*   Verify that the sparklines (Causal Distance, Connected Total, Connected Unique) render properly based on the selected Summery Function (Min, Max, Mean).

================ FlowLang DSL Flag Stress-Testing ================

*   Write a script that creates excessive parallel branches. Use the `-pl[x]` flag (Parallel Execution Limit) with low and high integers to verify the engine respects branch caps.
*   Test the `-bl[x]` flag (Branch Limit) to ensure the system strictly stops creating multi-way branches after the limit is reached.
*   Test the `-sr[x,y]` (Space Range) and `-mr[x,y]` (Match Range) flags to ensure rules only apply to the specified bounds of multi-way spaces and matched sub-vectors.
*   Inject stochastic flags like `-p_rule[0.5]` and `-p_space[0.1]` and evolve the system. Run multiple times to verify non-deterministic outputs.
*   Force overlapping spatial matches using `overlapped=True`.
*   Test the Conflict Marking Protocol by switching the `-cmp` flag between `"ignore"`, `"this"`, `"og"`, and `"both"`.
*   Combine the conflict marker with the Conflict Resolution Protocol (`-crp`) using `"branch"`, `"skip"`, and `"break"` to verify that overlapping rules yield the correct subsequent multi-way spaces.

================ Intentional Failure Injection ================

*   Write an intentionally malformed FlowLang script (e.g., missing semicolons, unmatched brackets).
*   Attempt to execute it and verify that the parser catches the error, routing a red formatted traceback to the "Program Log" without crashing the entire Textual application.
*   Ensure the "Show tracebacks" checkbox is enabled in the Execute tab to verify rich traceback rendering.
*   Write an infinite loop inside a `@macro` or Python evaluation block (if accessible). Attempt to use the "Stop" button in the toolbar to safely interrupt the execution thread.
*   Spam the "Execute" button extremely quickly. Verify that the `Worker` thread management triggers the "Threading Error: A flow thread is currently running" warning instead of spawning conflicting processes.
*   Provide invalid data ranges in the Explore plugin (e.g., `invalid:range` in the Event Range input). Verify that the Textual `notify` system gracefully warns you instead of crashing the UI.
*   Provide an invalid space coordinate (e.g., `(999, 999)`) in the Explore tab and verify it safely resets or warns you.