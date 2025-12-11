def wolfram_numbering_scheme(charset: str, index: int) -> list[tuple[str, str]]:
    """
    Generates Wolfram Elementary Cellular Automata rules for a given index.

    Args:
        charset: A string of two characters (e.g. "01" or "AB").
                 charset[0] is '0' (dead), charset[1] is '1' (alive).
        index: The Wolfram rule number (0-255).
    """
    if len(charset) != 2:
        raise ValueError("Charset must contain exactly 2 characters.")
    binary_patterns: list[tuple[int, int, int]] = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0),
        (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0)
    ]
    rule_bits = f'{index:08b}'  # Convert index to 8-bit binary string (e.g., 30 -> '00011110')
    rules = []
    for (b1, b2, b3), result_bit in zip(binary_patterns, rule_bits):
        selector = f"{charset[b1]}{charset[b2]}{charset[b3]}"
        replacement = charset[int(result_bit)]
        rules.append((selector, replacement))
    return rules


if __name__ == '__main__':
    print(wolfram_numbering_scheme('AB', 30))
