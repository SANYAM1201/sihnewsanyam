"""Automated dataset collection and indexing for multi-frequency sonar models."""

import os
from pathlib import Path

DATASETS_INFO = {
    "SCTD_3.0": {
        "description": "Standard Combat Training Dataset (Sonar Targets)",
        "frequency": "400kHz",
        "local_dir": "datasets/external/sctd_3.0",
    },
    "AquaScan_2023": {
        "description": "High-resolution side-scan sonar seabed benchmarks",
        "frequency": "900kHz",
        "local_dir": "datasets/external/aquascan",
    },
    "NOAA_Public": {
        "description": "Government hydroacoustic bathymetry & side-scan surveys",
        "frequency": "100kHz",
        "local_dir": "datasets/external/noaa_sonar",
    },
}


def prepare_dataset_directories():
    print("Initializing external dataset ingestion directories...")
    for name, info in DATASETS_INFO.items():
        p = Path(info["local_dir"])
        p.mkdir(parents=True, exist_ok=True)
        readme = p / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {name}\n\n"
                f"- Description: {info['description']}\n"
                f"- Nominal Frequency: {info['frequency']}\n"
                "- Status: Ingestion ready. Place sonogram frames (.png, .tif, .xtf) here.\n"
            )
        print(f"  [OK] {name} ({info['frequency']}) -> {info['local_dir']}")


if __name__ == "__main__":
    prepare_dataset_directories()
