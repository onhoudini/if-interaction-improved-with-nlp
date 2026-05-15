import struct
import sys
import re
from pathlib import Path
from typing import List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]


# -- Decod Z-characters --

_ALPHABET = [
    "abcdefghijklmnopqrstuvwxyz",   # A0
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",   # A1
    " \n0123456789.,!?_#'\"/\\-:()", # A2
]


def _unpack_zchars(data: bytes) -> List[int]:
    zchars: List[int] = []
    i = 0
    while i + 1 < len(data):
        word = (data[i] << 8) | data[i + 1]
        zchars += [(word >> 10) & 0x1F, (word >> 5) & 0x1F, word & 0x1F]
        if word & 0x8000:
            break
        i += 2
    return zchars


def _decode_zchars(zchars: List[int]) -> str:
    alphabet = 0
    result: List[str] = []
    i = 0

    while i < len(zchars):
        c = zchars[i]

        if c == 0:
            result.append(" ")
        elif c in (1, 2, 3):
            i += 1
        elif c == 4:
            alphabet = 1
        elif c == 5:
            alphabet = 2
        elif c == 6 and alphabet == 2:
            if i + 2 < len(zchars):
                zscii = (zchars[i + 1] << 5) | zchars[i + 2]
                if 32 <= zscii < 127:
                    result.append(chr(zscii))
                i += 2
        else:
            idx = c - 6
            if 0 <= idx < 26:
                result.append(_ALPHABET[alphabet][idx])
            alphabet = 0

        i += 1

    return "".join(result).strip()


# -- Filter words --

def is_valid_word(word: str) -> bool:
    return re.fullmatch(r"[a-zA-Z]+([\'-][a-zA-Z]+)*", word) is not None


# -- Read vocab -- 

def extract_dictionary(game_path: str) -> Tuple[List[str], List[str]]:
    data = Path(game_path).read_bytes()

    version    = data[0]
    dict_addr  = (data[0x08] << 8) | data[0x09]

    pos = dict_addr

    num_sep    = data[pos]; pos += 1
    separators = [chr(data[pos + i]) for i in range(num_sep)]
    pos += num_sep

    entry_length = data[pos]; pos += 1
    num_entries  = struct.unpack(">h", data[pos:pos + 2])[0]; pos += 2
    if num_entries < 0:
        num_entries = -num_entries

    text_bytes = 4 if version <= 3 else 6

    words: List[str] = []
    for i in range(num_entries):
        entry_addr = pos + i * entry_length
        encoded    = data[entry_addr:entry_addr + text_bytes]
        word       = _decode_zchars(_unpack_zchars(encoded))

        if word and is_valid_word(word):
            words.append(word.lower())

    return sorted(set(words)), separators


def save_dictionary(words: List[str], output_path: str) -> None:
    Path(output_path).write_text("\n".join(words) + "\n", encoding="utf-8")


def _print_summary(words: List[str], separators: List[str], game_path: str) -> None:
    print(f"Jogo      : {game_path}")
    print(f"Separadores: {separators}")
    print(f"Palavras  : {len(words)}\n")

    current = ""
    for word in words:
        letter = word[0].upper()
        if letter != current:
            current = letter
            print(f"\n[{current}]", end=" ")
        print(word, end=" ")
    print("\n")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT_ROOT / "frotz-master" / "games" / "zork1-r88-s840726.z3")

    words, separators = extract_dictionary(path)
    _print_summary(words, separators, path)

    script_dir = Path(__file__).resolve().parent
    out = script_dir / (Path(path).stem + "_dictionary.txt")

    save_dictionary(words, str(out))
    print(f"Dicionário salvo em: {out}")