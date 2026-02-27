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
