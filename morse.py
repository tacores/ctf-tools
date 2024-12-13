#! /usr/bin/python3

# usage
# $ echo "... --- ..." | python morse.py
# SOS

# Mapping Morse Code to Alphanumeric Characters
MORSE_CODE_DICT = {
    "-----": "0",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
}


def morse_to_text(morse_line):
    return "".join(
        MORSE_CODE_DICT.get(code, "?") for code in morse_line.split()
    )


def main():
    import sys

    for line in sys.stdin:
        print(morse_to_text(line.strip()))


if __name__ == "__main__":
    main()
