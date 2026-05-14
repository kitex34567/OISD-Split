#!/usr/bin/env python3
"""Download OISD big domainswild list and split into 70k-entry EDL files."""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

SOURCE_URL = "https://big.oisd.nl/domainswild"
OUTPUT_DIR = "lists"
PREFIX = "oisd_big_part"
CHUNK_SIZE = 70_000


def download_list(url: str) -> list[str]:
    print(f"Downloading {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "oisd-edl-autosplit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")
    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip OISD wildcard prefix (*.) for Palo Alto compatibility
        if line.startswith("*."):
            line = line[2:]
        entries.append(line)
    print(f"  -> {len(entries):,} entries parsed")
    return entries


def write_part(path: str, entries: list[str], part_num: int, total: int, ts: str) -> None:
    header = (
        f"# OISD Big Blocklist – Part {part_num}\n"
        f"# Source : {SOURCE_URL}\n"
        f"# Updated: {ts}\n"
        f"# Entries: {len(entries):,} (of {total:,} total)\n"
        f"# Format : plain domain (Palo Alto EDL compatible)\n#\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(header)
        fh.write("\n".join(entries))
        fh.write("\n")
    print(f"  wrote {path}  ({len(entries):,} entries)")


def remove_stale_parts(num_parts: int) -> None:
    """Delete part files whose index is higher than the current part count."""
    stale = 1
    while True:
        candidate = os.path.join(OUTPUT_DIR, f"{PREFIX}{num_parts + stale}.txt")
        if not os.path.exists(candidate):
            break
        os.remove(candidate)
        print(f"  removed stale file {candidate}")
        stale += 1


def generate_index(parts: list[str], ts: str, repo_slug: str) -> str:
    base_url = f"https://{repo_slug.replace('/', '.github.io/', 1)}/lists"
    rows = ""
    for part_file in parts:
        url = f"{base_url}/{part_file}"
        rows += (
            f"        <tr>\n"
            f"          <td>{part_file}</td>\n"
            f"          <td><a href=\"{url}\" target=\"_blank\">{url}</a></td>\n"
            f"        </tr>\n"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OISD EDL – Palo Alto / Prisma SSE</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
    h1   {{ color: #1a1a2e; }}
    table{{ border-collapse: collapse; width: 100%; }}
    th,td{{ border: 1px solid #ccc; padding: .5rem .75rem; text-align: left; }}
    th   {{ background: #f0f0f0; }}
    a    {{ color: #0066cc; }}
    code {{ background: #f5f5f5; padding: .1rem .3rem; border-radius: 3px; }}
    .meta{{ color: #555; font-size: .9rem; margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>OISD Big Blocklist – EDL Files</h1>
  <p class="meta">
    Source: <a href="{SOURCE_URL}">{SOURCE_URL}</a><br>
    Last updated: <strong>{ts}</strong>
  </p>
  <table>
    <thead>
      <tr><th>File</th><th>EDL URL (use in Palo Alto / Prisma SSE)</th></tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>
  <h2>How to use in Prisma SSE (Strata Cloud Manager)</h2>
  <ol>
    <li>Go to <em>Configuration → NGFW and Prisma Access → Objects → External Dynamic Lists → Add</em></li>
    <li>Set <strong>Type</strong> to <code>Domain List</code></li>
    <li>Paste one of the EDL URLs above as the <strong>Source</strong></li>
    <li>Set <strong>Check for updates</strong> to <code>Daily</code></li>
    <li>Repeat for each part file and reference all lists in your Security Policy</li>
  </ol>
</body>
</html>
"""


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = download_list(SOURCE_URL)
    total = len(entries)

    # Determine repo slug for URL generation (falls back to placeholder)
    repo_slug = os.environ.get("GITHUB_REPOSITORY", "<owner>/<repo>")

    chunks = [entries[i : i + CHUNK_SIZE] for i in range(0, total, CHUNK_SIZE)]
    part_files = []
    for idx, chunk in enumerate(chunks, start=1):
        filename = f"{PREFIX}{idx}.txt"
        write_part(os.path.join(OUTPUT_DIR, filename), chunk, idx, total, ts)
        part_files.append(filename)

    remove_stale_parts(len(chunks))

    # Write metadata.json
    metadata = {
        "updated": ts,
        "source": SOURCE_URL,
        "total_entries": total,
        "num_parts": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "parts": part_files,
    }
    meta_path = os.path.join(OUTPUT_DIR, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
    print(f"  wrote {meta_path}")

    # Write index.html
    index_html = generate_index(part_files, ts, repo_slug)
    with open("index.html", "w", encoding="utf-8") as fh:
        fh.write(index_html)
    print("  wrote index.html")

    print(f"Done. {total:,} entries → {len(chunks)} part file(s).")


if __name__ == "__main__":
    main()
