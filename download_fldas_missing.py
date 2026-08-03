"""
Fill in the gaps in the local FLDAS_NOAH01_C_GL_M.001 archive.

Reads the GES DISC subset manifest (subset_FLDAS_NOAH01_C_GL_M_001_*.txt) already
sitting in this folder, skips any monthly file already downloaded, and fetches the
rest -- same dataset, same 0.1 x 0.1 deg resolution, every variable (wind, humidity,
rainfall, temperature, soil moisture, ...) bundled in each monthly .nc file.

Prerequisites (one-time):
  1. NASA Earthdata Login account: https://urs.earthdata.nasa.gov
  2. In your Earthdata profile -> Applications -> Authorize New Applications ->
     approve "NASA GESDISC DATA ARCHIVE".
  3. A netrc file at C:\\Users\\<you>\\_netrc containing:
       machine urs.earthdata.nasa.gov login <username> password <password>
     (On Windows, curl/requests look for "_netrc", not ".netrc".)

Usage:
  python download_fldas_missing.py            # download everything missing
  python download_fldas_missing.py --dry-run   # just show what would be downloaded
"""
import argparse
import re
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
MANIFEST_GLOB = "subset_FLDAS_NOAH01_C_GL_M_001_*.txt"
MIN_VALID_SIZE_BYTES = 50 * 1024 * 1024  # real monthly files are ~110-130 MB; anything
                                          # smaller on disk is a partial/failed download


def find_manifest() -> Path:
    candidates = sorted(HERE.glob(MANIFEST_GLOB))
    if not candidates:
        sys.exit(f"No manifest file matching {MANIFEST_GLOB} found in {HERE}")
    return candidates[0]


def load_urls(manifest_path: Path) -> list[str]:
    urls = []
    for line in manifest_path.read_text().splitlines():
        line = line.strip()
        m = re.search(r"https?://\S+\.nc\b", line)
        if m:
            urls.append(m.group(0))
    return urls


def is_already_downloaded(target: Path) -> bool:
    return target.exists() and target.stat().st_size >= MIN_VALID_SIZE_BYTES


def download_one(url: str, target: Path) -> None:
    tmp = target.with_suffix(target.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    tmp.rename(target)


def remove_stray_duplicates() -> None:
    for dup in HERE.glob("*.001 (*.nc"):
        print(f"Removing stray duplicate: {dup.name}")
        dup.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="list missing files without downloading")
    args = parser.parse_args()

    manifest = find_manifest()
    urls = load_urls(manifest)
    print(f"Manifest: {manifest.name} ({len(urls)} files listed)")

    missing = [(url, HERE / url.rsplit("/", 1)[-1]) for url in urls]
    missing = [(url, target) for url, target in missing if not is_already_downloaded(target)]
    print(f"Already downloaded: {len(urls) - len(missing)} / {len(urls)}")
    print(f"Missing: {len(missing)} / {len(urls)}")

    if args.dry_run:
        for _, target in missing:
            print(f"  would download -> {target.name}")
        return

    if not missing:
        print("Nothing to download.")
        remove_stray_duplicates()
        return

    ok, failed = 0, []
    for i, (url, target) in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {target.name} ...", end=" ", flush=True)
        try:
            download_one(url, target)
            print(f"done ({target.stat().st_size / 1e6:.0f} MB)")
            ok += 1
        except Exception as e:
            print(f"FAILED ({e})")
            failed.append(target.name)

    print(f"\nDownloaded {ok}/{len(missing)}.")
    if failed:
        print(f"Failed ({len(failed)}), re-run this script to retry them:")
        for name in failed:
            print(f"  {name}")

    remove_stray_duplicates()


if __name__ == "__main__":
    main()
