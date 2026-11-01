#!/usr/bin/env python3
"""Standalone bootstrap for the SAKU-encrypted runner.tehrpa package."""

import os
import struct
import sys
import zlib
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RPA_FILE = BASE_DIR / "runner.tehrpa"
RUNNER_LABEL = BASE_DIR / "TEHrunner.py"
SALT_CHUNKS = [
    "MoY1A", "75-vi", ">2_j6", "6VjnP", "tJ,jr", "=RZeH", "RFRCq",
    "_ere3", ":yLt@", "#o}0v", "XEUr7", "EdM@:", "1o@mA", "RXxV6",
    "?#~dn", "p%r2t", "v:CDk", "qD?Ns", "4=:mc", "u%@k6",
]


class SakuyaEnigma:
    def __init__(self):
        salt_value = sum(map(ord, "".join(SALT_CHUNKS)))
        self.rotors = self._generate_rotors(salt_value)
        self.byte_rotors = [
            sorted(range(256), key=rotor.__getitem__) for rotor in self.rotors
        ]
        self.inverse_byte_rotors = []
        for rotor in self.byte_rotors:
            inverse = [0] * 256
            for value, encoded in enumerate(rotor):
                inverse[encoded] = value
            self.inverse_byte_rotors.append(inverse)

    @staticmethod
    def _generate_rotors(salt_value):
        rotors = []
        for rotor_index in range(5):
            rotor = list(range(2048))
            seed = (salt_value * (rotor_index + 1) + 1337) % 2048
            for index in range(2047, 0, -1):
                seed = (seed * 1103515245 + 12345) % 2048
                swap_index = seed % (index + 1)
                rotor[index], rotor[swap_index] = rotor[swap_index], rotor[index]
            rotors.append(rotor)
        return rotors

    @staticmethod
    def _advance_positions(positions):
        positions[0] = (positions[0] + 1) % 256
        for index in range(4):
            if positions[index] != 0:
                break
            positions[index + 1] = (positions[index + 1] + 1) % 256
        return positions

    def decrypt(self, data, day_offset):
        positions = [(day_offset * factor) % 256 for factor in (11, 17, 23, 31, 47)]
        result = bytearray()
        for byte in data:
            value = byte
            for index in range(4, -1, -1):
                value = (self.inverse_byte_rotors[index][value] - positions[index]) % 256
            result.append(value)
            self._advance_positions(positions)
        return bytes(result)


def get_day_offset(base_date="2024-05-01"):
    return max(0, (datetime.now() - datetime.strptime(base_date, "%Y-%m-%d")).days)


def decrypt_archive():
    if not RPA_FILE.is_file():
        raise FileNotFoundError(f"Encrypted package not found: {RPA_FILE.name}")

    data = RPA_FILE.read_bytes()
    if len(data) < 8 or data[:4] != b"SAKU":
        raise ValueError("Invalid or truncated SAKU package header")

    day_offset = struct.unpack(">I", data[4:8])[0]
    if get_day_offset() < day_offset - 1:
        raise ValueError("Package date check failed; check the system date")

    try:
        compressed = SakuyaEnigma().decrypt(data[8:], day_offset)
        return zlib.decompress(compressed)
    except (zlib.error, IndexError) as error:
        raise ValueError(f"Could not decrypt or decompress the SAKU package: {error}") from error


def main():
    args = sys.argv[1:]
    if args not in (["--load"], ["--verify"]):
        raise SystemExit("Usage: python TEHloader.py [--load|--verify]")

    source = decrypt_archive()
    compile(source, str(RUNNER_LABEL), "exec")
    if args == ["--verify"]:
        print(f"SAKU package verified: {RPA_FILE.name}")
        return

    os.environ["TEH_OFFICIAL_LOADER"] = "1"
    sys.argv = [str(RUNNER_LABEL), "--load"]
    main_module = sys.modules["__main__"]
    main_module.__file__ = str(RUNNER_LABEL)
    exec(compile(source, str(RUNNER_LABEL), "exec"), main_module.__dict__)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, OSError, ValueError) as error:
        print(f"[Loader error] {error}", file=sys.stderr)
        raise SystemExit(1) from error
