from typing import Callable, Any
from lang.interpreter import FlowLang
from core.topologies.tooling.rff_encoding import chr_rff
from studio.stdplgns.sss._system_classifier import classify_system
import studio.stdplgns.sss._ruleset_tests as tests
from studio.stdplgns.sss._ruleset_tests import from_reduced_rank_quinary_code, from_rf_ruleset, index_to_qcode, RuleSetData
from pathlib import Path


def ruleset_display(ruleset: list[tuple[tuple[int, ...], tuple[int, ...]]]) -> str:
    return ", ".join([f"{''.join(chr_rff(c + 65) for c in m)} -> {''.join(chr_rff(c + 65) for c in r)}" for m, r in ruleset])


def ruleset_to_flow_code(initial_state: str, ruleset: list[tuple[tuple[int, ...], tuple[int, ...]]]) -> str:
    # Simulate via FlowLang Generation
    flow_code = f'@init("{initial_state}");\n'
    for match, replace in ruleset:
        m_str: str = str(match)
        r_str: str = str(replace)
        if not m_str and not r_str:
            continue
        elif not m_str:
            flow_code += f"[0] > {r_str};\n"
        elif not r_str:
            flow_code += f"{m_str} >< ;\n"
        else:
            flow_code += f"{m_str} -> {r_str};\n"
    return flow_code


def run_sessie_enumeration(
        workflow_config: dict,
        on_progress: Callable[[float], None],
        on_result: Callable[[RuleSetData, str, int, str, str], None],
        is_cancelled: Callable[[], bool],
        on_log: Callable[[str], None] | Any
) -> None:
    # ================ Read Config ================
    # ruleset source
    ruleset_src_path: str | False = workflow_config.get('ruleset', False)
    ruleset_src_path_suffix: str | None = None
    ruleset_src: str | False = False
    if ruleset_src_path:
        with open(ruleset_src_path, 'r') as f:
            ruleset_src = f.read()
        ruleset_src_path_suffix: str = Path(ruleset_src_path).suffix

    # Search Space
    search = workflow_config.get('search_space', {})
    start_idx = search.get('start_index', 1)
    end_idx = search.get('end_index', 100)

    # Simulation
    sim = workflow_config.get('simulation', {})
    raw_init = sim.get('initial_state', 'A')
    halt_on_inert = sim.get('halt_on_inert', True)

    # Convert input string to ordinals dynamically
    if isinstance(raw_init, str):
        init_state = "".join(raw_init)
    else:
        init_state = "".join(chr_rff(c) for c in raw_init)

    max_steps = sim.get('max_steps', 200)

    filter_names = workflow_config.get('filters', [])
    filter_funcs = [getattr(tests, f"test_for_{f}") for f in filter_names if hasattr(tests, f"test_for_{f}")]

    total_runs = max(1, end_idx - start_idx + 1)
    current_idx = start_idx

    # ================ Execute Pipeline ================
    while current_idx <= end_idx:
        if is_cancelled():
            on_log("[bold orange]Execution cancelled by user.[/]")
            break

        if current_idx < 1:
            current_idx += 1
            continue

        qcode = index_to_qcode(current_idx)
        if ruleset_src:
            flow = FlowLang()
            flow.interpret(ruleset_src, qcode, bootstrapped=ruleset_src_path_suffix)
            rs_data = from_rf_ruleset(flow.ruleset)
            rs_data["QCode"] = qcode
            rs_data["Index"] = current_idx  # TODO: IS PROBLEMATIC
        else:
            rs_data = from_reduced_rank_quinary_code(qcode)

        jumped = False

        # Apply Declarative Filters
        for func, name in zip(filter_funcs, filter_names):
            target_idx = func(rs_data)
            if target_idx is not None:
                on_result(rs_data, ruleset_display(rs_data['RuleSet']), 0, "Filtered", name)
                current_idx = target_idx
                jumped = True
                break

        if jumped:
            continue

        # Simulate via FlowLang Generation
        try:
            if not ruleset_src:
                flow = FlowLang()
                flow.interpret(ruleset_to_flow_code(init_state, rs_data['RuleSet']))
            # noinspection unbound-local-variable
            flow.evolve(max_steps, halt_on_inert=halt_on_inert)
            cls_data = classify_system(flow, max_steps)
            # ruleset: RuleSetData, ruleset_str: str, steps: int, cls: str, status: str
            on_result(
                rs_data, ruleset_display(rs_data['RuleSet']),
                flow.current_event_idx, cls_data["classification"], "Simulated"
            )
        except Exception as e:
            on_log(f"[bold red]Simulation Error at Index {current_idx}:[/] {e}")

        current_idx += 1
        on_progress(min(((current_idx - start_idx) / total_runs) * 100, 100))

    if not is_cancelled():
        on_log("[bold green]Sessie Pipeline Complete![/]")
        on_progress(100.0)
