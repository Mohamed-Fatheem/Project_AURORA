"""Physical measurements and precision retained; no inferred real truth labels."""

import csv

from aurora.real_data import OFFICIAL_DIR, load_apxs_product


def feasibility_report():
    path = OFFICIAL_DIR / "apxs_sol00046.csv"
    records, provenance = load_apxs_product(path, OFFICIAL_DIR / "apxs_sol00046.xml")
    with path.open(encoding="utf8", newline="") as stream:
        reader = csv.reader(stream, skipinitialspace=True)
        next(reader)
        rows = [{"analyte": row[0].strip(), "concentration": float(row[1]),
                 "statistical_precision": float(row[2]), "unit": record.unit,
                 "timestamp_utc": record.timestamp_utc, "product_id": record.product_id,
                 "quality_flag": record.quality_flag}
                for record, row in zip(records, reader, strict=True)]
    return {"status": "feasibility_only", "provenance": provenance, "measurements": rows,
            "processing": "No unit conversion, normalization, synthetic index mapping, or synthetic labels",
            "uncertainty": "CSV statistical precision retained; systematic accuracy and covariance not supplied here",
            "evaluation_possible": ["product identity and provenance", "finite values and precision", "schema and label units"],
            "evaluation_not_supported": ["fault precision/recall", "geological classification accuracy", "autonomy utility"],
            "missing_evidence": ["independent matched geology labels", "fault and repair event truth",
                                 "calibrated APXS-to-hypothesis likelihood", "measurement covariance and accuracy model"],
            "sources": ["https://pds-geosciences.wustl.edu/missions/msl/apxs.htm",
                        "https://pds-geosciences.wustl.edu/workshops/DPS_2020_Presentations/2020-1027-DPS-APXS-Tutorial.pdf"],
            "unit_caution": "Product label says concentration wt%; other APXS exports may use microgram/gram for trace elements. Do not mix formats."}
