from lark import Lark, Transformer, Token, Tree
import json
import os
from pprint import pprint


grammar: str = r"""
    start: (global_flags | block | instruction_sequence | directive | COMMENT)*
    
    // -------------------------------------------------------------------------
    // Top-Level Structure (The file is a sequence of these elements)
    // -------------------------------------------------------------------------
    
    // A statement for global flags, appearing alone (e.g., -ncd)
    global_flags: flags
    
    // A instruction block: (-flags) { sequence of instructions... }
    block: "(" flag+ ")" "{" instruction_sequence "}"
    
    // Rules inside a group block (must end with a semicolon)
    instruction_sequence: (instruction ";")+

    // -------------------------------------------------------------------------
    // Core Instruction Definition (The unit of work)
    // -------------------------------------------------------------------------
    
    instruction: [selector] operator [selector] [flags]

    // --- Selectors ---
    selector: regex_term
            | llm_term
            | range_term
            | literal_term

    // We define these as specific terminals to prevent ambiguity
    regex_term: REGEX_LITERAL
    llm_term: STRING_LITERAL
    range_term: RANGE_LITERAL
    literal_term: SIMPLE_LITERAL

    // --- Operators ---
    operator: OP_REVERSE
            | OP_SWAP
            | OP_OVERWRITE
            | OP_DELETE
            | OP_SHIFT_R
            | OP_SHIFT_L
            | OP_SUB
            | OP_INSERT
    
    // --- Flags ---
    flags: flag+
    flag: FLAG_DEF

    // -------------------------------------------------------------------------
    // Terminals (Lexer Rules)
    // -------------------------------------------------------------------------

    // Priority: Higher priority tokens are matched first.

    // 1. Complex Literals
    REGEX_LITERAL: /\/[^\/]+\//
    STRING_LITERAL: /"[^"]+"/
    RANGE_LITERAL: /\[\s*-?\d*\s*(,\s*-?\d*\s*)?\]/   // Matches [1], [1,2], [1,] or [,2]

    // 2. Operators (Longer matches first)
    OP_REVERSE:   ">><<"
    OP_SWAP:      ">-<"
    OP_OVERWRITE: "-->"
    OP_DELETE:    "><"
    OP_SHIFT_R:   ">>"
    OP_SHIFT_L:   "<<"
    OP_SUB:       "->"
    OP_INSERT:    ">"
    

    // 3. Flags
    FLAG_DEF: /-[a-zA-Z][a-zA-Z0-9_]*(\[[^\]]*\])?/
    
    // 4. Identifiers & Targets (Simplified to ensure no conflict with flags/operators)
    SIMPLE_LITERAL: /[a-zA-Z0-9_]+/
    
    // 5. Structural Tokens
    %import common.SIGNED_INT  // can import other similar standards
    %import common.WS
    %import common.NEWLINE
    COMMENT: /\/\/[^\n]*/
    
    // 6. Directives (Example: @Universe: "A(B)A" or @Steps: 100)
    DIRECTIVE_KEY: /[a-zA-Z][a-zA-Z0-9_.]+/
    DIRECTIVE_VALUE: /[^(\);)]+/
    directive: "@" DIRECTIVE_KEY "(" DIRECTIVE_VALUE ");"
    
    // -------------------------------------------------------------------------
    // Ignore Rules
    // -------------------------------------------------------------------------
    %ignore WS
    %ignore NEWLINE
    %ignore COMMENT
"""


class FlowLangTransformer(Transformer):
    """
    Transforms the Lark AST for Flow Lang into a structured Python dictionary,
    handling directives, global flags, rule groups (by distributing flags), and individual instructions.
    """

    def start(self, items):
        """
        The root of the file. Collects all top-level elements into a single list
        of instructions and a dictionary of ruleset flags.
        """
        directives = {}
        global_flags = {}
        instructions = []
        for array in items:
            for item in array:
                if item['type'] == 'directive':
                    directives[item['key']] = item['value']
                elif item['type'] == 'global_flags':
                    global_flags.update(item['flags'])
                elif item['type'] == 'instruction':
                    instructions.append(item)
        return {
            'directives': directives,
            'global_flags': global_flags,  # the flags the set the defaults
            'instructions': instructions
        }

    def directive(self, items):
        return [{
            'type': 'directive',
            'key': items[0].value,
            'value': items[1].value,
        }]

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
        return {
            "type": 'instruction',
            "operator_type": items[1]['type'],
            "selector": items[0],
            "operator": items[1]['symbol'],
            "target": items[2],
            "flags": _ if (_:=items[3]) else {}
        }

    def selector(self, items):
        # Unwrap selector child (regex_term, literal_term, etc.)
        return items[0]

    def operator(self, items):
        # Unwrap operator
        return {
            "type": items[0].type,
            "symbol": items[0].value
        }

    def target(self, items):
        # Propagate up
        return items[0].value

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
        parts = content.split(',')

        try:
            # Helper to convert part to int or None
            def parse_part(part):
                p = part.strip()
                # Lark returns empty strings for missing parts like in [,2]
                return int(p) if p else None

            start = parse_part(parts[0])
            end = None

            if len(parts) > 1:
                end = parse_part(parts[1])
            elif start is not None:
                # Case: [x] where it should be treated as [x,x]
                end = start

        except ValueError:
            # Handle cases where non-integer is inside range brackets
            return {"type": "range", "error": "Invalid range format"}

        return {"type": "range", "start": start, "end": end}

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
        # Remove leading -
        raw = raw[1:]

        # Default value for boolean/unit flags (e.g., -a, -nt)
        args = True
        name = raw

        if '[' in raw and raw.endswith(']'):
            name_part, args_part = raw.split('[', 1)
            name = name_part
            args_str = args_part[:-1]  # remove trailing ]

            # Split args by comma
            arg_list = []
            if args_str:
                for a in args_str.split(','):
                    a = a.strip()
                    # Try to parse as int, otherwise keep as string
                    try:
                        if a:  # Ignore empty strings from double commas or leading/trailing comma
                            arg_list.append(int(a))
                    except ValueError:
                        arg_list.append(a)

            # If the list is empty (e.g., -flag[]), args remains an empty list.
            args = arg_list

        # Clean up name: remove - (already done) and convert to lowercase if needed
        return {name: args}


class FlowLangParser:
    def __init__(self, use_transformer: bool = True):
        """Builds the parser.

        TODO: add cache option to skip building on every run...
        """

        self._flow_parser = Lark(grammar, parser='lalr', transformer=FlowLangTransformer() if use_transformer else None)

    def parse(self, text) -> dict | Tree:
        try:
            return self._flow_parser.parse(text)
        except Exception as e:
            raise e
            return {"error": str(e), "input": text}


def main():
    # The test cases provided in the prompt
    expr_list = [
        # Basic substitution
        "AB -> ABB",
        "AB -> ABB",
        "/A+B/ -> A",

        # Insertion
        "[0] > XYZ",
        "/B/ > C",
        "[3,5] > DEF",

        # Overwrite
        "AB --> CD",
        "/[0-9]+/ --> NUM",
        "[1,4] --> XXXX",

        # Deletion
        "AB ><",
        "/C+/ ><",
        "[2,] ><",

        # Shifting
        "AB >> 2",
        "AB << 1",
        "/D/ >> 3",

        # Using flags
        "AB -> ABB -nt",
        "/X+/ -> Y -nb",
        "AB -> ABB -bl[2,5]",
        "AB -> ABB -el[1,3]",
        "AB -> ABB -runs[10]",
        "AB -> ABB -o[left_to_right]",
        "AB -> ABB -a",
        "AB -> ABB -g[2]",

        # LLM selector
        "\"match all vowels\" -> V",
        "\"find repeating substrings\" --> REP",

        # Complex combinations
        "/A+/ -> AA -bl[,2] -el[1,4]",
        "[0,3] >> 1 -runs[5]",
        "\"digits at end\" >< -nb",
    ]

    parser = FlowLangParser()
    t = parser.parse("""
    // Directives
    @Universe.test(ABBB);
    @Test(isaac);
    
    // Global Flags
    -test[1, 2, 3]
    -flow
    
    // Group
    (-group[test]) {
        [1,2] -> ABB -f[1,2];
        a -> b;
    }
    
    // Lone Rule
    b >><< /[A]+/ -cursor[1, 2];
    """)
    pprint(t)

    # # for expr in ('[1, 3] -> ABB -isaac',):
    # # for expr in expr_list:
    # for expr in (input() for _ in range(100)):
    #     result = parser.parse(expr)
    #     pprint(result)
    #     # # Taking the first result since we parse line by line here
    #     # if isinstance(result, list):
    #     #     result = result[0]
    #     #
    #     # print(f"Expr: {expr}")
    #     # print(json.dumps(result, indent=2))
    #     # print("-" * 40)


if __name__ == "__main__":
    main()
