import pytest
import sys
from unittest.mock import MagicMock, patch

# ================ Mocking the Wolfram Environment ================
# We must mock wolframclient before importing wolfram.py to prevent the
# hardcoded ImportError when the Wolfram Engine is absent on the test runner.
mock_wl = MagicMock()
mock_wlexpr = MagicMock()
sys.modules['wolframclient'] = MagicMock()
sys.modules['wolframclient.evaluation'] = MagicMock()
sys.modules['wolframclient.language'] = MagicMock()
sys.modules['wolframclient.language'].wl = mock_wl
sys.modules['wolframclient.language'].wlexpr = mock_wlexpr

from lang.bootstrapped.python import bootstrapped_py_parse
from lang.bootstrapped.wolfram import bootstrapped_wl_parse, _escape_wl_literal


# ================ Python Bootstrapper Tests ================

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


@patch('lang.bootstrapped.wolfram.open_wl_session')
@patch('lang.bootstrapped.wolfram.parse')
def test_wolfram_bootstrapper_ast_generation(mock_parse, mock_open_session):
    """
    Validates that bootstrapped_wl_parse correctly handles placeholders,
    injects args/kwargs, and properly flattens nested lists returned by the WL session.
    """
    # Setup the Mocked WL Session
    mock_session = MagicMock()
    mock_open_session.return_value = mock_session

    # Simulate the WL Reap output containing a nested list of strings
    # The bootstrapper's flatten function must unravel this.
    mock_session.evaluate.return_value = [[["A -> B;"], "C -> D;"]]

    # Run the bootstrapper
    script = '''
    ---
    {i} -> B;
    ---
    '''
    # We provide timeout and kwargs to verify they route to the WL set/evaluate methods.
    bootstrapped_wl_parse(script, 42, session_name="test_session", timeout=5.0, my_kwarg="val")

    # Verify Session Management and Namespace Injection
    mock_open_session.assert_called_once_with("test_session")

    # Verify that python args and kwargs were passed to wl.Set to inject into the namespace.
    assert mock_session.evaluate.call_count >= 3

    # Verify script wrapping and evaluation
    # Extract the script that was passed into session.evaluate(wlexpr(...))
    evaluate_calls = mock_session.evaluate.call_args_list
    wlexpr_arg = evaluate_calls[-1][0][0]

    # Because we mocked wlexpr, it recorded the string it was initialized with.
    # We must extract that string from the mock's call history.
    generated_wl_script = mock_wlexpr.call_args[0][0]

    # Check execution wrapper ensuring Reap and CompoundExpression are wrapping the code.
    assert generated_wl_script.startswith("Reap[CompoundExpression[")
    assert generated_wl_script.endswith("]][[2]]")

    # Check the placeholder translation logic for safety against WL Message errors.
    assert 'ToString[Check[ToExpression["i"], $Failed]]' in generated_wl_script

    # Verify the flattening logic sent the correctly joined string to parse().
    mock_parse.assert_called_once_with("A -> B;C -> D;")
