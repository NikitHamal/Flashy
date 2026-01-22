import random
import time
from typing import Any, Callable, Dict, List, Optional, Union
import asyncio
from .fingerprint import generate_fingerprint

# ==================== Config ====================

CUSTOM_BASE64_CHARS = "DGi0YA7BemWnQjCl4_bR3f8SKIF9tUz/xhr2oEOgPpac=61ZqwTudLkM5vHyNXsVJ"

# Hash field positions (need random regeneration)
HASH_FIELDS: Dict[int, str] = {
    16: "split",  # plugin hash: "count|hash" (replace only hash part)
    17: "full",   # canvas hash
    18: "full",   # UA hash 1
    31: "full",   # UA hash 2
    34: "full",   # URL hash
    36: "full",   # doc attribute hash (10-100)
}


# ==================== LZW Compression (JS-faithful port) ====================

def lzw_compress(data: Optional[str], bits: int, char_func: Callable[[int], str]) -> str:
    if data is None:
        return ""

    dictionary: Dict[str, int] = {}
    dict_to_create: Dict[str, bool] = {}

    c = ""
    wc = ""
    w = ""

    enlarge_in = 2
    dict_size = 3
    num_bits = 2

    result: List[str] = []
    value = 0
    position = 0

    for i in range(len(data)):
        c = data[i]

        if c not in dictionary:
            dictionary[c] = dict_size
            dict_size += 1
            dict_to_create[c] = True

        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            if w in dict_to_create:
                # output "w" as a raw char (8-bit or 16-bit)
                if ord(w[0]) < 256:
                    # write num_bits zeros
                    for _ in range(num_bits):
                        value = (value << 1)
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1

                    char_code = ord(w[0])
                    for _ in range(8):
                        value = (value << 1) | (char_code & 1)
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1
                        char_code >>= 1
                else:
                    # write a 1 marker
                    char_code = 1
                    for _ in range(num_bits):
                        value = (value << 1) | char_code
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1
                        char_code = 0

                    char_code = ord(w[0])
                    for _ in range(16):
                        value = (value << 1) | (char_code & 1)
                        if position == bits - 1:
                            position = 0
                            result.append(char_func(value))
                            value = 0
                        else:
                            position += 1
                        char_code >>= 1

                enlarge_in -= 1
                if enlarge_in == 0:
                    enlarge_in = 2 ** num_bits
                    num_bits += 1

                del dict_to_create[w]
            else:
                # output dictionary code for w
                char_code = dictionary[w]
                for _ in range(num_bits):
                    value = (value << 1) | (char_code & 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code >>= 1

            enlarge_in -= 1
            if enlarge_in == 0:
                enlarge_in = 2 ** num_bits
                num_bits += 1

            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    # flush remaining w
    if w != "":
        if w in dict_to_create:
            if ord(w[0]) < 256:
                for _ in range(num_bits):
                    value = (value << 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1

                char_code = ord(w[0])
                for _ in range(8):
                    value = (value << 1) | (char_code & 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code >>= 1
            else:
                char_code = 1
                for _ in range(num_bits):
                    value = (value << 1) | char_code
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code = 0

                char_code = ord(w[0])
                for _ in range(16):
                    value = (value << 1) | (char_code & 1)
                    if position == bits - 1:
                        position = 0
                        result.append(char_func(value))
                        value = 0
                    else:
                        position += 1
                    char_code >>= 1

            enlarge_in -= 1
            if enlarge_in == 0:
                enlarge_in = 2 ** num_bits
                num_bits += 1
            del dict_to_create[w]
        else:
            char_code = dictionary[w]
            for _ in range(num_bits):
                value = (value << 1) | (char_code & 1)
                if position == bits - 1:
                    position = 0
                    result.append(char_func(value))
                    value = 0
                else:
                    position += 1
                char_code >>= 1

        enlarge_in -= 1
        if enlarge_in == 0:
            enlarge_in = 2 ** num_bits
            num_bits += 1

    # end-of-stream marker (2)
    char_code = 2
    for _ in range(num_bits):
        value = (value << 1) | (char_code & 1)
        if position == bits - 1:
            position = 0
            result.append(char_func(value))
            value = 0
        else:
            position += 1
        char_code >>= 1

    # pad to complete a char
    while True:
        value = (value << 1)
        if position == bits - 1:
            result.append(char_func(value))
            break
        position += 1

    return "".join(result)


# ==================== Encoding ====================

def custom_encode(data: Optional[str], url_safe: bool) -> str:
    if data is None:
        return ""

    base64_chars = CUSTOM_BASE64_CHARS

    compressed = lzw_compress(
        data,
        6,
        lambda index: base64_chars[index]  # index should be 0..63
    )

    if not url_safe:
        mod = len(compressed) % 4
        if mod == 1:
            return compressed + "==="
        if mod == 2:
            return compressed + "=="
        if mod == 3:
            return compressed + "="
        return compressed

    return compressed


# ==================== Helpers ====================

def random_hash() -> int:
    return random.randint(0, 0xFFFFFFFF)


def generate_device_id() -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(20))


# ==================== Data parse/process ====================

def parse_real_data(real_data: str) -> List[str]:
    return real_data.split("^")


def process_fields(fields: List[str]) -> List[Union[str, int]]:
    processed: List[Union[str, int]] = list(fields)
    current_timestamp = int(time.time() * 1000)

    for idx, typ in HASH_FIELDS.items():
        if idx >= len(processed):
            continue

        if typ == "split":
            # field 16: "count|hash" -> replace only hash
            val = str(processed[idx])
            parts = val.split("|")
            if len(parts) == 2:
                processed[idx] = f"{parts[0]}|{random_hash()}"
        elif typ == "full":
            if idx == 36:
                processed[idx] = random.randint(10, 100)  # 10-100
            else:
                processed[idx] = random_hash()

    # field 33: current timestamp
    if 33 < len(processed):
        processed[33] = current_timestamp

    return processed

# ==================== Cookie generation ====================

def generate_cookies(
    real_data: Optional[str] = None,
    fingerprint_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if fingerprint_options is None:
        fingerprint_options = {}

    fingerprint = real_data or generate_fingerprint(fingerprint_options)

    fields = parse_real_data(fingerprint)
    processed_fields = process_fields(fields)

    # ssxmod_itna (37 fields)
    ssxmod_itna_data = "^".join(map(str, processed_fields))
    ssxmod_itna = "1-" + custom_encode(ssxmod_itna_data, True)

    # ssxmod_itna2 (18 fields)
    ssxmod_itna2_data = "^".join(map(str, [
        processed_fields[0],    # device id
        processed_fields[1],    # sdk version
        processed_fields[23],   # mode (P/M)
        0, "", 0, "", "", 0,    # event-related (empty in P mode)
        0, 0,
        processed_fields[32],   # constant (11)
        processed_fields[33],   # current timestamp
        0, 0, 0, 0, 0
    ]))
    ssxmod_itna2 = "1-" + custom_encode(ssxmod_itna2_data, True)

    return {
        "ssxmod_itna": ssxmod_itna,
        "ssxmod_itna2": ssxmod_itna2,
        "timestamp": int(processed_fields[33]),
        "rawData": ssxmod_itna_data,
        "rawData2": ssxmod_itna2_data,
    }
