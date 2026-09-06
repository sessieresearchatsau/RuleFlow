from ruleflow.lang.bootstrapped.python import bootstrapped_py_parse
from ruleflow.lang.bootstrapped.wolfram import _escape_wl_literal


def test_python_bootstrapper_kwargs_and_indentation():
    """
    Verifies that Python code correctly receives kwargs and respects standard
    Python loop indentation when appending fragments to the __out list.
    """
    script = '''
factor = kwargs.get('factor', 1)
for i in range(2):
    ---
    "{i * factor}" -> ABC;
    ---
'''
    # Pass kwargs natively into the bootstrapper
    ast = bootstrapped_py_parse(script, factor=10)

    assert len(ast['instructions']) == 2
    assert ast['instructions'][0]['selector'][0]['value'] == b'0'
    assert ast['instructions'][1]['selector'][0]['value'] == b'10'


def test_python_bootstrapper_multiple_blocks():
    """
    Ensures multiple distinct blocks in the same script are aggregated safely
    using the multiline regex dotall pattern.
    """
    script = '''
---
A -> B;
---
x = 5
---
B -> C;
---
'''
    ast = bootstrapped_py_parse(script)
    assert len(ast['instructions']) == 2
    assert ast['instructions'][0]['selector'][0]['value'] == b'A'
    assert ast['instructions'][1]['selector'][0]['value'] == b'B'


# ================ Wolfram Bootstrapper Tests ================
def test_wolfram_literal_escaping():
    """
    Verifies the _escape_wl_literal function accurately replaces carriage returns,
    newlines, quotes, and backslashes for safe injection into Wolfram strings.
    """
    unsafe_string = 'Line1\r\n"Quote"\\Backslash\nLine2'
    escaped = _escape_wl_literal(unsafe_string)

    # Carriage returns and newlines should become \n, which then becomes \\n. Quotes and Backslashes are also escaped.
    assert escaped == 'Line1\\n\\"Quote\\"\\\\Backslash\\nLine2'
