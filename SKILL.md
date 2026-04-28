# Skill: Max-Intensity m/z per Filter

Find the highest-intensity peak (m/z + intensity) across all scans for each
unique filter string in a RAW file, and return the results as a sorted list.

---

## Algorithm

1. `file filters` → list of all unique filter strings in the file
2. For each filter → `search by_filter` → matching scan numbers
3. For each scan → `scan stats` → `base_peak_mass`, `base_peak_intensity`
4. Keep the best (highest `base_peak_intensity`) per filter
5. Sort results by intensity descending

---

## Code

```python
import subprocess, json
from collections import defaultdict

RAW_FILE = "sample.raw"   # ← change to your file

def _run(*args):
    cmd = ["rawfilereader"] + list(args) + ["--file", RAW_FILE]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(json.loads(r.stderr)["error"])
    return json.loads(r.stdout)


def max_intensity_per_filter(raw_file: str) -> list[dict]:
    """Return [{mz, intensity, filter}, ...] sorted by intensity descending."""
    global RAW_FILE
    RAW_FILE = raw_file

    filters = _run("file", "filters")["filters"]
    results = []

    for flt in filters:
        scan_numbers = _run("search", "by_filter", "--filter_string", flt)["scan_numbers"]
        if not scan_numbers:
            continue

        best_mz, best_intensity = None, -1
        for sn in scan_numbers:
            stats = _run("scan", "stats", "--scan_number", str(sn))
            bp_intensity = stats.get("base_peak_intensity", 0) or 0
            if bp_intensity > best_intensity:
                best_intensity = bp_intensity
                best_mz = stats.get("base_peak_mass")

        results.append({"mz": best_mz, "intensity": best_intensity, "filter": flt})

    results.sort(key=lambda r: r["intensity"], reverse=True)
    return results


# ── run ────────────────────────────────────────────────────────────────────
rows = max_intensity_per_filter(RAW_FILE)

print(f"{'m/z':>12}  {'intensity':>14}  filter")
print("-" * 90)
for row in rows:
    mz_str  = f"{row['mz']:.4f}" if row["mz"] is not None else "N/A"
    print(f"{mz_str:>12}  {row['intensity']:14.3e}  {row['filter']}")
```

---

## Example output

```
         m/z       intensity  filter
------------------------------------------------------------------------------------------
   445.1185    9.123e+07  FTMS + p NSI Full ms [200.00-2000.00]
   612.3041    3.457e+06  FTMS + c NSI d Full ms2 445.12@hcd28.00 [100.00-1500.00]
   204.0865    1.102e+06  FTMS + c NSI d Full ms2 612.30@hcd28.00 [100.00-800.00]
```

---

## As a pandas DataFrame

```python
import pandas as pd

df = pd.DataFrame(max_intensity_per_filter(RAW_FILE))
df = df[["mz", "intensity", "filter"]]   # reorder columns
print(df.to_string(index=False))
```

---

## Notes

- `base_peak_mass` / `base_peak_intensity` come from the Thermo scan header —
  they reflect the most intense centroid in each scan without loading the full
  spectrum array, making this fast even for large files.
- For files with many filters and thousands of scans per filter the loop will
  take proportionally longer. To speed things up, narrow the search first with
  `--start_scan` / `--end_scan` on `search by_filter`.
