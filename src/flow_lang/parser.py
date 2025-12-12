from core import enumerator
from lark import Lark, Transformer
from numerical_helpers import str_to_num, INF
from typing import Any, cast


BUILTIN_IMPORT_PATHS: dict[str, str] = {
    'ca_presets': "@merge(0);\n-pl[inf]\n-mr[0,inf]"  # default import code to streamline the use of CAs in the 0th group.
}


def _r_parse(value: str) -> dict[str, Any]:
    """Recursive parsing helper for top-level directives"""
    return cast(dict[str, Any], cast(object, FlowLangParser(use_transformer=True).parse(value)))


def import_directive(path: str) -> list[dict[str, Any]]:
    """Import from a file or preset"""
    value: str = BUILTIN_IMPORT_PATHS.get(path, None)
    if value is None:
        with open(f'{path}.flow') as f:
            value = f.read()
    result = _r_parse(value)
    result['type'] = 'imported'  # we create an "imported" object type.
    return [result]


def decode_directive(method: str, *args) -> list[dict[str, Any]]:
    """Just use the general functions for rule enumeration and convert that to a string, parse, and return."""
    if method == 'wns':
        src: str = ''.join([
            f'{selector} --> _{target};'
            for selector, target in enumerator.wolfram_numbering_scheme(*args)
        ])
        return _r_parse(src)['instructions']
    raise ValueError(f'Enumeration method `{method}` is not implemented')


def intercept_top_level_directive(d: dict[str, Any]) -> list[dict[str, Any]]:
    name: str = d['key']
    if name == 'import':
        return import_directive(d['value'][0])
    elif name == 'decode':
        return decode_directive(*d['value'])
    else:  # if there is nothing to intercept just propagate
        return [d]


class FlowLangTransformer(Transformer):
    """
    Transforms the Lark AST for Flow Lang into a structured Python dictionary,
    handling directives, global flags, rule groups (by distributing flags), and individual instructions.
    """

    # helper
    @staticmethod
    def parse_part(part) -> int | float | str | bool | None:
        p: str = part.strip()
        if p == '':
            return None
        elif p == 'true':
            return True
        elif p == 'false':
            return False
        try:
            return str_to_num(p)
        except ValueError:
            return p

    def start(self, items):
        """
        The root of the file. Collects all top-level elements into a single list
        of instructions and a dictionary of ruleset flags.
        """
        directives = []
        global_flags = {}
        instructions = []
        for array in items:
            for item in array:
                if item['type'] == 'directive':
                    directives.append((item['key'], item['value']))
                elif item['type'] == 'global_flags':
                    global_flags.update(item['flags'])
                elif item['type'] == 'instruction':
                    instructions.append(item)
                elif item['type'] == 'imported':
                    directives.extend(item['directives'])
                    global_flags.update(item['global_flags'])
                    instructions.extend(item['instructions'])
        return {
            'directives': directives,
            'global_flags': global_flags,  # the flags the set the defaults
            'instructions': instructions
        }

    def directive(self, items):
        if items[1]:  # detect None for directives such as `@Test.me()` with no arguments
            value: tuple = tuple((self.parse_part(p) for p in items[1].value.split(',')))  # parse the args
        else:
            value: tuple = ()
        return intercept_top_level_directive({
            'type': 'directive',
            'key': items[0].value,
            'value': value
        })

    def global_flags(self, items):
        return [{'type': 'global_flags', 'flags': items[0]}]  # we wrap in a list so that the start() visitor can do less work

    def block(self, items):
        flags = items[0]  # temp
        instructions = items[1]
        for instruction in instructions:  # distribute the flags of the block into its constituents
            for k, v in flags.items():
                instruction['flags'].setdefault(k, v)
        return instructions

    def instruction_sequence(self, items):
        return items

    def instruction(self, items):
        out = {
            "type": 'instruction',
            "selector": [],
            "operator": items[-3],
            "target": items[-2],
            "flags": _ if (_:=items[-1]) else {}
        }
        for i in range(len(items) - 3):
            t: str = items[i]['type']
            if t == 'selector':
                out['selector'].append(items[i])
        if (op_type:=out['operator']['operator_type']) in ('OP_SHIFT_R', 'OP_SHIFT_L'):  # special case for these rules
            out['target'] = str_to_num(out['target']['value']) * (-1 if op_type == 'OP_SHIFT_L' else 1)
        return out

    def selector(self, items):
        # Unwrap selector child (regex_term, literal_term, etc.)
        items[0]['selector_type'] = items[0]['type']
        items[0]['type'] = 'selector'
        return items[0]

    def operator(self, items):
        # Unwrap operator
        return {
            "type": 'operator',
            "operator_type": items[0].type,
            "symbol": items[0].value
        }

    # --- Terminals to Values (Unchanged) ---
    def regex_term(self, items):
        return {"type": "regex", "value": items[0].value[1:-1]}

    def literal_term(self, items):
        return {"type": "literal", "value": items[0].value}

    def llm_term(self, items):
        return {"type": "llm_prompt", "value": items[0].value[1:-1]}

    def range_term(self, items):
        # Parse [x,y] or [x]
        content = items[0].value[1:-1]  # strip []

        # Helper to convert part to int or None
        def parse_part(part):
            p = part.strip()
            # Lark returns empty strings for missing parts like in [,2]
            return str_to_num(p) if p else None

        parts = content.split(',')
        if len(parts) == 1:
            start = parse_part(parts[0])
            end = start
        else:  # this will be the case: len(parts) == 2
            start = parse_part(parts[0])
            end = parse_part(parts[1])
            if start is None: start = 0
            if end is None: end = INF

        return {"type": "range", "value": (start, end)}

    # --- Flags ---
    def flags(self, items):
        """
        Collects all individual flag dictionaries into a single dictionary
        that can be merged into a rule, group header, or ruleset.
        """
        flag_dict = {}
        for f in items:
            # f is a dictionary like {'flag_name': value} returned by self.flag
            flag_dict.update(f)
        return flag_dict

    def flag(self, items):
        # Parse the raw flag string "-name[args]"
        raw = items[0].value
        # Remove leading "-"
        raw = raw[1:]

        # Default value for boolean/unit flags (e.g., -a, -nt)
        args: bool = True
        name = raw

        if '[' in raw and raw.endswith(']'):
            name_part, args_part = raw.split('[', 1)
            name = name_part
            args_str = args_part[:-1]  # remove trailing "]"
            if args_str:
                arg_parts = args_str.split(',')
                if len(arg_parts) == 1:
                    args: int | float | str = self.parse_part(arg_parts[0])
                else:
                    args: tuple[int | float | str, ...] = tuple((self.parse_part(p) for p in arg_parts))

        return {name: args}


def FlowLangParser(use_transformer: bool = True) -> Lark:
    """Creates the Lark parser object from which .parse(text) can be called."""
    return Lark.open(
        grammar_filename='./grammar.lark',
        parser='lalr',
        transformer=FlowLangTransformer() if use_transformer else None
    )


if __name__ == "__main__":
    # example (different rules can be added to ensure correct parsing):
    from pprint import pprint
    parser = FlowLangParser()
    t = parser.parse("""
    // Rule 30
    @init(AAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAA);
    @import(eca_presets);
    
    // define the rules
    @merge(0);
    (-pl[inf] -mr[0,inf]) {
        @decode(wns, AB, 30);
    }
    
    // Run n times
    @evolve(16);
    """)
    print(type(t))
    pprint(t)
