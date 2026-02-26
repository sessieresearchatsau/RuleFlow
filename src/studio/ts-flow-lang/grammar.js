module.exports = grammar({
  name: 'flow-lang',

  // Extras are tokens that can appear anywhere (like whitespace and comments)
  extras: $ => [
    /\s/,
    $.comment
  ],

  rules: {
    // The root node can be any sequence of blocks, instructions, directives, or global flags
    source_file: $ => repeat(choice(
      $.block,
      $.instruction,
      $.directive,
      $.flag
    )),

    // A block allows flags inside the parenthesis, and instructions/directives inside the braces
    block: $ => seq(
      '(',
      repeat($.flag),
      ')',
      '{',
      repeat(choice(
        $.instruction,
        $.directive
      )),
      '}'
    ),

    // Flattened for syntax highlighting: any valid sequence of terms/operators ending in ';'
    instruction: $ => seq(
      repeat1(choice(
        $.regex,
        $.string,
        $.range,
        $.literal,
        $.operator,
        $.flag
      )),
      ';'
    ),

    // Directives capture the key and value as specific fields for easy targeting
    directive: $ => seq(
      '@',
      field('name', $.literal),
      '(',
      optional(field('value', $.directive_value)),
      ')',
      ';'
    ),

    // --- Terminals & Tokens ---

    // Anything inside the directive parentheses that isn't a closing paren or semicolon
    directive_value: $ => /[^();\n]+/,

    // Regexes: Starts with /, contains anything but / or newline, ends with /
    regex: $ => /\/[^\/\n]+\//,

    // Strings: Standard double quotes
    string: $ => /"[^"\n]*"/,

    // Ranges: Reused your exact regex, just as a direct token
    range: $ => /\[\s*(?:-?\d+|inf|-inf)?\s*(?:,\s*(?:-?\d+|inf|-inf)?\s*)?\]/,

    // Operators
    operator: $ => choice(
      '>><<', '-->', '><', '>>', '<<', '->', '>'
    ),

    // Flags: Requires a leading hyphen and a letter, optionally followed by bracketed arguments
    flag: $ => /-[a-zA-Z][a-zA-Z0-9_]*(?:\[[^\]\n]*\])?/,

    // Literals: Simple identifiers, numbers, and dots
    literal: $ => /[a-zA-Z0-9_.*]+/,

    // Comments: Starts with // and goes to the end of the line
    comment: $ => token(seq('//', /.*/))
  }
});
