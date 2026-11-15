"""Provenance contract for external planetary measurements; no synthetic labels."""

import csv
import hashlib
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

PRODUCT_BASE = ("https://pds-geosciences.wustl.edu/msl/"
                "msl-m-apxs-4_5-rdr-v1/mslapx_1xxx/data/sol00046/"
                "apa_401575435rwp00460042100_______p1")
OFFICIAL_DIR = Path(__file__).resolve().parents[2] / "data/official"


@dataclass(frozen=True)
class PDSRecord:
    product_id: str
    source_url: str
    instrument: str
    timestamp_utc: str
    value: float
    unit: str
    calibrated: bool
    quality_flag: str
    archive: str = "NASA PDS Geosciences"

    def __post_init__(self) -> None:
        parsed = urlparse(self.source_url)
        if (not self.product_id or parsed.scheme != "https" or
                parsed.hostname != "pds-geosciences.wustl.edu" or
                self.instrument != "APXS" or self.unit != "wt_pct" or
                not math.isfinite(self.value) or self.value < 0 or
                not isinstance(self.calibrated, bool) or
                self.quality_flag not in ("not_provided", "good", "suspect", "bad") or
                self.archive != "NASA PDS Geosciences"):
            raise ValueError("invalid PDS provenance, value, unit or quality metadata")
        try:
            timestamp = datetime.fromisoformat(self.timestamp_utc)
        except ValueError as exc:
            raise ValueError("invalid timestamp") from exc
        if timestamp.tzinfo is None:
            raise ValueError("timestamp must include timezone")

    def to_dict(self) -> dict:
        return {**asdict(self), "simulator_truth_labels": None}


def external_validation_status(records: list[PDSRecord]) -> dict:
    return {"status": "qualitative_schema_only" if records else "adapter_only",
            "records_validated": len(records),
            "ground_truth_fault_labels": "unavailable",
            "synthetic_likelihood_compatible": False,
            "claim": "provenance/schema checks only; no real-world fault or geology accuracy"}


def load_apxs_product(csv_path: Path, label_path: Path) -> tuple[list[PDSRecord], dict]:
    """Read the specific PDS sol-46 oxide table with its PDS4 label."""
    root = ElementTree.parse(label_path).getroot()
    namespace = {"p": "http://pds.nasa.gov/pds4/pds/v1"}
    product_id = root.findtext(".//p:logical_identifier", namespaces=namespace)
    timestamp = root.findtext(".//p:start_date_time", namespaces=namespace)
    if (product_id != "urn:nasa:pds:msl_apxs_calibrated:data:"
            "apa_401575435rwp00460042100_______p1" or not timestamp or
            "Concentration (wt%)" not in label_path.read_text(encoding="utf8")):
        raise ValueError("unsupported or incomplete APXS product label")
    records = []
    analytes = []
    uncertainties = []
    with csv_path.open(encoding="utf8", newline="") as stream:
        reader = csv.reader(stream, skipinitialspace=True)
        header = [part.strip() for part in next(reader)]
        if header != ["oxide", "APXS analysis ver 2", "statistical uncertainty (precision)"]:
            raise ValueError("unexpected APXS CSV schema")
        for row in reader:
            if len(row) != 3:
                raise ValueError("invalid APXS CSV row")
            name, value, uncertainty = (part.strip() for part in row)
            number, precision = float(value), float(uncertainty)
            if not name or number < 0 or not math.isfinite(precision) or precision < 0:
                raise ValueError("invalid APXS concentration or uncertainty")
            analytes.append(name)
            uncertainties.append(precision)
            records.append(PDSRecord(product_id, PRODUCT_BASE + ".csv", "APXS", timestamp,
                                     number, "wt_pct", True, "not_provided"))
    if not records or len(set(analytes)) != len(analytes):
        raise ValueError("empty or duplicate APXS table")
    provenance = {"product_id": product_id, "source_csv": PRODUCT_BASE + ".csv",
                  "source_label": PRODUCT_BASE + ".xml",
                  "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                  "label_sha256": hashlib.sha256(label_path.read_bytes()).hexdigest(),
                  "analytes": analytes, "uncertainty_unit": "wt_pct",
                  "uncertainty_min": min(uncertainties),
                  "uncertainty_max": max(uncertainties),
                  "quality_flags": "not_provided"}
    return records, provenance


def official_product_status() -> dict:
    csv_path = OFFICIAL_DIR / "apxs_sol00046.csv"
    label_path = OFFICIAL_DIR / "apxs_sol00046.xml"
    if not csv_path.exists() or not label_path.exists():
        return external_validation_status([])
    records, provenance = load_apxs_product(csv_path, label_path)
    return {**external_validation_status(records), "product": provenance}
