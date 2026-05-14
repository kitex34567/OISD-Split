# OISD EDL Auto-Split for Palo Alto / Prisma SSE

This repository automatically downloads the [OISD Big](https://oisd.nl/) domain blocklist daily,
splits it into chunks of 70,000 entries, and publishes the files via **GitHub Pages** as
**External Dynamic Lists (EDL)** ready for use in Palo Alto Firewalls and Prisma SSE.

## How it works

| Step | Description |
|------|-------------|
| Source | `https://big.oisd.nl/domainswild` (wildcard format) |
| Transform | `*.` prefix stripped → plain domain (Palo Alto compatible) |
| Split | 70,000 entries per file |
| Schedule | GitHub Actions cron **04:00 UTC daily** |
| Delivery | GitHub Pages (static hosting, no server needed) |

## EDL URLs

After enabling GitHub Pages (see Setup), the EDL files are available at:

```
https://<your-username>.github.io/<repo-name>/lists/oisd_big_part1.txt
https://<your-username>.github.io/<repo-name>/lists/oisd_big_part2.txt
https://<your-username>.github.io/<repo-name>/lists/oisd_big_part3.txt
# … and so on depending on the current list size
```

An overview page with all URLs is served at the repository root:

```
https://<your-username>.github.io/<repo-name>/
```

## Setup

### 1. Fork / use this repository

Click **Use this template** or fork the repository.  
The repository **must be public** for free GitHub Pages hosting.

### 2. Enable GitHub Pages

1. Go to **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / root (`/`)
4. Save – Pages will be live within a minute

### 3. Run the workflow for the first time

Go to **Actions → Update OISD EDL Lists → Run workflow**.  
This populates `lists/` and `index.html` immediately.

### 4. Configure EDLs in Prisma SSE (Strata Cloud Manager)

1. **Configuration → NGFW and Prisma Access → Objects → External Dynamic Lists → Add**
2. **Type:** `Domain List`
3. **Source:** paste one of the GitHub Pages URLs above
4. **Check for updates:** `Daily`
5. Repeat for every part file
6. Reference the EDL objects in your Security Policy

### 4b. Configure EDLs in a standalone Palo Alto NGFW (PAN-OS)

1. **Objects → External Dynamic Lists → Add**
2. **Type:** `Domain List`
3. **Source:** GitHub Pages URL
4. **Repeat interval:** `Daily`
5. Commit the configuration

## Files

```
.
├── split_oisd.py                        # Main download & split script
├── index.html                           # Auto-generated overview page (GitHub Pages)
├── .nojekyll                            # Disables Jekyll processing
├── .github/
│   └── workflows/
│       └── update-edl.yml               # Daily automation workflow
└── lists/
    ├── metadata.json                    # Timestamp, entry count, part count
    ├── oisd_big_part1.txt               # EDL file – part 1
    ├── oisd_big_part2.txt               # EDL file – part 2
    └── oisd_big_part3.txt               # EDL file – part 3 (approx.)
```

## Running locally

```bash
python split_oisd.py
```

No external dependencies – uses Python standard library only.

## License

The automation scripts in this repository are released under the [MIT License](LICENSE).  
The blocklist data itself is provided by [OISD](https://oisd.nl/) under their own terms.
