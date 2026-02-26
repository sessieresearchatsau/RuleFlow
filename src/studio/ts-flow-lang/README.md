# FlowLang Tree-sitter Grammar for RuleFlow Studio

This guide contains everything required to build, compile, and integrate the custom **FlowLang** Tree-sitter grammar into your Textual application. 

Because Tree-sitter (v0.22.0+) removed on-the-fly C compilation, grammars are now handled as standard Python C-extensions. To avoid writing complex C binding wrappers by hand, we use an explicit `tree-sitter.json` configuration file. This forces the official CLI to generate the exact Python packaging boilerplate (`setup.py`, `pyproject.toml`, and the python module) automatically and correctly.



---

## 1. Project Directory Layout

Before running any commands, ensure your project root looks exactly like this. 

```text
tree-sitter-flowlang/
├── package.json             # Manages the local Tree-sitter CLI
├── tree-sitter.json         # Configures the CLI to build Python bindings
├── grammar.js               # The Tree-sitter grammar definition
├── queries/
│   └── highlights.scm       # Maps your syntax nodes to Textual colors
└── ruleflow_studio.py       # Your main Textual application
```


---

## 2. Required Configuration Files

Create the following files in your project directory.

### `tree-sitter.json`

This is the most critical file for the new workflow. Setting `"python": true` tells the CLI to automatically generate all the Python `setup.py` and `pyproject.toml` boilerplate for you.

```json
{
  "grammars": [
    {
      "name": "flowlang",
      "camelcase": "Flowlang",
      "scope": "source.flowlang",
      "path": ".",
      "file-types": ["flow"]
    }
  ],
  "metadata": {
    "version": "0.1.0",
    "license": "MIT",
    "description": "FlowLang grammar for RuleFlow Studio",
    "authors": "RuleFlow Author"
  },
  "bindings": {
    "c": true,
    "python": true
  }
}

```

### `package.json`

Provides the local Node environment to run the compiler.

```json
{
  "name": "tree-sitter-flowlang",
  "version": "0.1.0",
  "devDependencies": {
    "tree-sitter-cli": "^0.22.0"
  }
}

```

### `queries/highlights.scm`

Maps the parsed syntax tree nodes to Textual's highlighting system.

```scheme
(comment) @comment
(string) @string
(regex) @string.regexp
(range) @number
(operator) @operator
(flag) @variable.parameter

(literal) @variable
(directive name: (literal) @function.macro)
(directive value: (directive_value) @string.special)

"(" @punctuation.bracket
")" @punctuation.bracket
"{" @punctuation.bracket
"}" @punctuation.bracket
";" @punctuation.delimiter
"@" @punctuation.special

```

---

## 3. Build & Install Instructions

You need **Node.js**, **Python 3.8+**, and a **C Compiler** (like GCC or Clang) installed on your system.

**Step 1: Install the Tree-sitter CLI locally**

```bash
npm install

```

**Step 2: Generate the Parser and Python Bindings**
This reads `grammar.js` and `tree-sitter.json` to generate the `src/` folder (C code) and the Python packaging files (`setup.py`, etc.).

```bash
npx tree-sitter generate

```

**Step 3: Compile and Install the Python Package**
This invokes your system's C compiler to build the shared library and installs it into your active Python environment.

```bash
pip install .

```

---

## 4. Textual Integration
- https://textual.textualize.io/widgets/text_area/#syntax-highlighting-dependencies
- https://textual.textualize.io/widgets/text_area/#adding-support-for-custom-languages
- https://github.com/grantjenks/py-tree-sitter-languages
- https://github.com/tree-sitter/py-tree-sitter
- https://tree-sitter.github.io/tree-sitter/
- https://github.com/tree-sitter/tree-sitter/blob/master/crates/cli/README.md

Once installed via `pip`, the grammar is available to Python as `tree_sitter_flowlang`. You can now pass its memory pointer directly to Textual's `TextArea`.

### `ruleflow_studio.py`

```python
from textual.app import App
from textual.widgets import TextArea
from tree_sitter import Language
import tree_sitter_flowlang

# 1. Initialize the Language using the exposed C function pointer
FlowLang = Language(tree_sitter_flowlang.language())

class RuleFlowStudio(App):
    def compose(self):
        textarea = TextArea()
        
        # 2. Register the language and query file with the TextArea
        textarea.register_language(
            "flowlang",
            FlowLang,
            highlight_query=open("queries/highlights.scm").read()
        )
        
        # Load some example text
        textarea.text = "(-ncd) {\n  /regex/ -> literal;\n  @Universe(ABA);\n};"
        yield textarea

if __name__ == "__main__":
    RuleFlowStudio().run()

```
