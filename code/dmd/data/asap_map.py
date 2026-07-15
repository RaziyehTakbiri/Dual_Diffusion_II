"""Generate the ANNOTATION_MAP csv from ASAP's metadata.csv (E4.1 helper).

Recommended usage runs everything on ASAP's OWN performance MIDIs (they are
the MAESTRO performances, sometimes cut to match annotations - so using ASAP
paths avoids the start/end offset problem entirely):

  from dmd.data.asap_map import main
  main(["--asap_root", "/dbfs/.../asap-dataset", "--out", ".../asap_map.csv"])

Then: MIDI_GLOB = "<asap_root>/**/*.mid*", GRID = "asap",
      ANNOTATION_MAP = ".../asap_map.csv"
(and rerun with GRID = "fixed" + the same map for the paired comparison).

ASAP is CC BY-NC-SA 4.0; cite Foscarin et al., ISMIR 2020.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asap_root", required=True,
                    help="folder containing metadata.csv")
    ap.add_argument("--out", required=True, help="output map csv path")
    args = ap.parse_args(argv)

    meta = os.path.join(args.asap_root, "metadata.csv")
    n, missing = 0, 0
    with open(meta, newline="") as fh, open(args.out, "w", newline="") as out:
        rd = csv.DictReader(fh)
        # the published column name is misspelled ('anotations'); accept both
        ann_col = next(c for c in rd.fieldnames
                       if c.strip().lower() in ("performance_anotations",
                                                "performance_annotations"))
        wr = csv.writer(out)
        for row in rd:
            midi = os.path.join(args.asap_root, row["midi_performance"].strip())
            ann = os.path.join(args.asap_root, row[ann_col].strip())
            if os.path.exists(midi) and os.path.exists(ann):
                wr.writerow([midi, ann])
                n += 1
            else:
                missing += 1
                print(f"[missing] {midi if not os.path.exists(midi) else ann}",
                      file=sys.stderr)
    print(f"wrote {n} performance->annotation pairs to {args.out} "
          f"({missing} rows skipped for missing files)")
    if n == 0:
        raise SystemExit("no pairs written - check --asap_root")


if __name__ == "__main__":
    main()
