from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .geometry import GeometryRecord, save_xyz
from .io_utils import write_json


_ATOMIC_SYMBOLS = {
    1: "H",
    2: "He",
    3: "Li",
    4: "Be",
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    10: "Ne",
    11: "Na",
    12: "Mg",
    13: "Al",
    14: "Si",
    15: "P",
    16: "S",
    17: "Cl",
    18: "Ar",
}

_ATOMIC_MASSES = {
    1: 1.00782503223,
    2: 4.00260325413,
    3: 7.0160034366,
    4: 9.012183065,
    5: 11.00930536,
    6: 12.0,
    7: 14.00307400443,
    8: 15.99491461957,
    9: 18.99840316273,
    10: 19.9924401762,
    11: 22.989769282,
    12: 23.985041697,
    13: 26.98153853,
    14: 27.97692653465,
    15: 30.97376199842,
    16: 31.9720711744,
    17: 34.968852682,
    18: 39.9623831237,
}


@dataclass
class GaussianTSData:
    log_path: Path
    charge: int
    multiplicity: int
    scf_energy: float | None
    route_section: str | None
    coordinates: np.ndarray
    atomic_numbers: list[int]
    frequencies: list[float]
    reduced_masses: list[float]
    force_constants: list[float]
    normal_modes: list[np.ndarray]
    num_imaginary_frequencies: int

    @property
    def symbols(self) -> list[str]:
        return [_ATOMIC_SYMBOLS[number] for number in self.atomic_numbers]

    @property
    def geometry_record(self) -> GeometryRecord:
        return GeometryRecord(
            sample_id="ts_seed",
            symbols=self.symbols,
            coordinates=self.coordinates,
            charge=self.charge,
            multiplicity=self.multiplicity,
            source="gaussian_ts_log",
            source_kind="ts_seed",
            metadata={
                "source_log": str(self.log_path.resolve()),
                "num_imaginary_frequencies": self.num_imaginary_frequencies,
            },
        )

    def to_mlatom_json(self) -> dict[str, Any]:
        atoms: list[dict[str, Any]] = []
        for atom_index, (atomic_number, symbol, coord) in enumerate(
            zip(self.atomic_numbers, self.symbols, self.coordinates, strict=True)
        ):
            atoms.append(
                {
                    "nuclear_charge": atomic_number,
                    "atomic_number": atomic_number,
                    "element_symbol": symbol,
                    "nuclear_mass": _ATOMIC_MASSES.get(atomic_number),
                    "xyz_coordinates": np.asarray(coord, dtype=float).tolist(),
                    "normal_modes": [mode[atom_index].tolist() for mode in self.normal_modes],
                }
            )

        return {
            "id": "ts_seed",
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "atoms": atoms,
            "frequencies": [float(value) for value in self.frequencies],
            "force_constants": [float(value) for value in self.force_constants],
            "reduced_masses": [float(value) for value in self.reduced_masses],
            "scf_energy": self.scf_energy,
            "source_log": str(self.log_path.resolve()),
            "route_section": self.route_section,
            "num_imaginary_frequencies": self.num_imaginary_frequencies,
        }

    def summary_payload(self) -> dict[str, Any]:
        imaginary_frequencies = [float(value) for value in self.frequencies if float(value) < 0.0]
        return {
            "source_log": str(self.log_path.resolve()),
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "num_atoms": len(self.atomic_numbers),
            "symbols": self.symbols,
            "scf_energy": self.scf_energy,
            "route_section": self.route_section,
            "num_frequencies": len(self.frequencies),
            "num_imaginary_frequencies": self.num_imaginary_frequencies,
            "imaginary_frequencies": imaginary_frequencies,
            "first_imaginary_frequency": imaginary_frequencies[0] if imaginary_frequencies else None,
            "num_reduced_masses": len(self.reduced_masses),
            "num_force_constants": len(self.force_constants),
        }


def _find_charge_and_multiplicity(text: str) -> tuple[int, int]:
    matches = re.findall(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", text)
    if not matches:
        raise ValueError("Could not find charge/multiplicity in Gaussian log.")
    charge_text, multiplicity_text = matches[-1]
    return int(charge_text), int(multiplicity_text)


def _find_last_route_section(lines: list[str]) -> str | None:
    route_lines: list[str] = []
    collecting = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if route_lines:
                route_lines = []
            route_lines.append(stripped)
            collecting = True
            continue
        if collecting:
            if not stripped:
                break
            route_lines.append(stripped)

    if not route_lines:
        return None
    return " ".join(route_lines)


def _parse_standard_orientation_block(lines: list[str], start_index: int) -> tuple[np.ndarray, list[int]]:
    data_start = start_index + 5
    coordinates: list[list[float]] = []
    atomic_numbers: list[int] = []

    for line in lines[data_start:]:
        stripped = line.strip()
        if stripped.startswith("-----"):
            break
        fields = stripped.split()
        if len(fields) < 6:
            continue
        atomic_numbers.append(int(fields[1]))
        coordinates.append([float(fields[3]), float(fields[4]), float(fields[5])])

    if not coordinates:
        raise ValueError("Failed to parse coordinates from Gaussian standard orientation block.")
    return np.asarray(coordinates, dtype=float), atomic_numbers


def _find_last_standard_orientation(lines: list[str]) -> tuple[np.ndarray, list[int]]:
    indices = [index for index, line in enumerate(lines) if "Standard orientation:" in line]
    if not indices:
        raise ValueError("Could not find any Gaussian standard orientation block.")

    last_error: Exception | None = None
    for index in reversed(indices):
        try:
            return _parse_standard_orientation_block(lines, index)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    raise ValueError("Failed to parse the final Gaussian standard orientation block.") from last_error


def _find_last_scf_energy(text: str) -> float | None:
    matches = re.findall(r"SCF Done:\s+E\([^)]+\)\s+=\s+(-?\d+\.\d+)", text)
    if not matches:
        return None
    return float(matches[-1])


def _parse_frequency_blocks(lines: list[str], natoms: int) -> tuple[list[float], list[float], list[float], list[np.ndarray]]:
    frequencies: list[float] = []
    reduced_masses: list[float] = []
    force_constants: list[float] = []
    normal_modes: list[np.ndarray] = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("Frequencies --"):
            continue

        block_frequencies = [float(value) for value in stripped.split("--", 1)[1].split()]
        num_modes_in_block = len(block_frequencies)
        if num_modes_in_block == 0:
            continue

        reduced_mass_index = index + 1
        while reduced_mass_index < len(lines) and "Red. masses --" not in lines[reduced_mass_index]:
            reduced_mass_index += 1
        if reduced_mass_index >= len(lines):
            raise ValueError("Found a Gaussian frequency block without reduced masses.")
        block_reduced_masses = [float(value) for value in lines[reduced_mass_index].split("--", 1)[1].split()]
        if len(block_reduced_masses) != num_modes_in_block:
            raise ValueError("Gaussian reduced masses do not match the number of frequencies in the block.")

        force_constant_index = reduced_mass_index + 1
        while force_constant_index < len(lines) and "Frc consts  --" not in lines[force_constant_index]:
            force_constant_index += 1
        if force_constant_index >= len(lines):
            raise ValueError("Found a Gaussian frequency block without force constants.")
        block_force_constants = [float(value) for value in lines[force_constant_index].split("--", 1)[1].split()]
        if len(block_force_constants) != num_modes_in_block:
            raise ValueError("Gaussian force constants do not match the number of frequencies in the block.")

        header_index = index + 1
        while header_index < len(lines) and "Atom  AN" not in lines[header_index]:
            header_index += 1
        if header_index >= len(lines):
            raise ValueError("Found a Gaussian frequency block without a normal-coordinate table header.")

        block_modes = [np.zeros((natoms, 3), dtype=float) for _ in range(num_modes_in_block)]
        row_index = header_index + 1
        atoms_read = 0
        while row_index < len(lines) and atoms_read < natoms:
            row = lines[row_index].strip()
            if not row:
                row_index += 1
                continue

            fields = row.split()
            if len(fields) < 2 or not fields[0].isdigit() or not fields[1].isdigit():
                break

            atom_index = int(fields[0]) - 1
            numeric_values = fields[2:]
            expected_values = 3 * num_modes_in_block
            if len(numeric_values) < expected_values:
                raise ValueError(
                    "Gaussian normal-coordinate table ended unexpectedly while parsing frequency blocks."
                )

            for mode_index in range(num_modes_in_block):
                offset = 3 * mode_index
                block_modes[mode_index][atom_index] = [
                    float(numeric_values[offset]),
                    float(numeric_values[offset + 1]),
                    float(numeric_values[offset + 2]),
                ]
            atoms_read += 1
            row_index += 1

        if atoms_read != natoms:
            raise ValueError("Failed to read all atoms from a Gaussian normal-coordinate table.")

        frequencies.extend(block_frequencies)
        reduced_masses.extend(block_reduced_masses)
        force_constants.extend(block_force_constants)
        normal_modes.extend(block_modes)

    if not (len(frequencies) == len(reduced_masses) == len(force_constants) == len(normal_modes)):
        raise ValueError("Parsed Gaussian vibrational properties have inconsistent lengths.")
    if not frequencies:
        raise ValueError("No Gaussian frequencies were parsed from the log file.")
    return frequencies, reduced_masses, force_constants, normal_modes


def parse_gaussian_ts_log(log_path: str | Path) -> GaussianTSData:
    log_path = Path(log_path).resolve()
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if "Normal termination of Gaussian" not in text:
        raise ValueError(f"Gaussian log did not terminate normally: {log_path}")

    lines = text.splitlines()
    charge, multiplicity = _find_charge_and_multiplicity(text)
    coordinates, atomic_numbers = _find_last_standard_orientation(lines)
    frequencies, reduced_masses, force_constants, normal_modes = _parse_frequency_blocks(
        lines,
        natoms=len(atomic_numbers),
    )
    num_imaginary_frequencies = sum(1 for value in frequencies if value < 0.0)

    if num_imaginary_frequencies != 1:
        raise ValueError(
            f"Expected exactly 1 imaginary frequency for a TS seed, found {num_imaginary_frequencies} in {log_path}."
        )

    return GaussianTSData(
        log_path=log_path,
        charge=charge,
        multiplicity=multiplicity,
        scf_energy=_find_last_scf_energy(text),
        route_section=_find_last_route_section(lines),
        coordinates=coordinates,
        atomic_numbers=atomic_numbers,
        frequencies=frequencies,
        reduced_masses=reduced_masses,
        force_constants=force_constants,
        normal_modes=normal_modes,
        num_imaginary_frequencies=num_imaginary_frequencies,
    )


def write_ts_seed_outputs(
    *,
    ts_data: GaussianTSData,
    json_output_path: str | Path,
    xyz_output_path: str | Path,
    summary_output_path: str | Path,
) -> dict[str, Any]:
    json_output_path = Path(json_output_path)
    xyz_output_path = Path(xyz_output_path)
    summary_output_path = Path(summary_output_path)

    write_json(json_output_path, ts_data.to_mlatom_json())
    save_xyz(ts_data.geometry_record, xyz_output_path, comment="ts_seed extracted from Gaussian log")

    summary = {
        **ts_data.summary_payload(),
        "ts_seed_json": str(json_output_path.resolve()),
        "ts_seed_xyz": str(xyz_output_path.resolve()),
        "summary_file": str(summary_output_path.resolve()),
    }
    write_json(summary_output_path, summary)
    return summary
