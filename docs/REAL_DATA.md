# Official APXS product: limited external schema check

Downloaded 2026-11-14 from the [NASA PDS Geosciences APXS archive](https://pds-geosciences.wustl.edu/missions/msl/apxs.htm).
The selected calibrated RDR product is
`urn:nasa:pds:msl_apxs_calibrated:data:apa_401575435rwp00460042100_______p1`
from Curiosity sol 46. The [CSV](https://pds-geosciences.wustl.edu/msl/msl-m-apxs-4_5-rdr-v1/mslapx_1xxx/data/sol00046/apa_401575435rwp00460042100_______p1.csv)
and [PDS4 label](https://pds-geosciences.wustl.edu/msl/msl-m-apxs-4_5-rdr-v1/mslapx_1xxx/data/sol00046/apa_401575435rwp00460042100_______p1.xml)
are stored under `data/official/` for reproducibility.

The label gives observation start `2012-09-22T08:46:44.722Z`, instrument APXS,
and concentration and statistical uncertainty in weight percent. The local
CSV has 16 oxide/element rows. Its SHA-256 is
`73b72f39db63928fbbfac44ac5400991add06a5027ba4e9e14a206910aaff749`;
the label SHA-256 is
`cfbe607cb053f65c852a80d882602317bb45977b9e67aad6d5fed956a1691662`.
The adapter verifies product identity, time, column schema, units, finite
nonnegative values, uncertainties, and unique analyte names. Per-row quality
flags are not supplied in this simple table; the adapter marks them
`not_provided` rather than declaring measurements good.

This product is **not** converted into AURORA's dimensionless synthetic index.
No legitimate likelihood mapping, paired second sensor product, independent
geology label, or instrument fault truth is available in this adapter. Thus
`qualitative_schema_only` means provenance and parsing checks passed; it does
not mean external validation of geology inference, fault diagnosis, model
adequacy, or autonomous decisions. No synthetic fault label is attached to
these real measurements.
