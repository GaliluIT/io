#!/usr/bin/env python3
"""Make the CV PDF from the CV page, so the PDF always matches content/cv.yml.

    python build.py
    python make_cv_pdf.py          # writes the PDF into _site/ (what gets published)
    python make_cv_pdf.py --save   # also updates the copy kept in assets/cv/

It prints the CV page with Chrome or Chromium, using the page's print layout:
black on white, no menus, and your name, email, website and LinkedIn at the top.
A phone number is never included.
GitHub runs this automatically when it publishes the site (.github/workflows/pages.yml).
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"


def find_chrome():
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    # Chromium installed by Playwright, or the usual Mac and Windows places
    candidates = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") + [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save", action="store_true", help="also update the copy in assets/cv/")
    args = parser.parse_args()

    site = yaml.safe_load((ROOT / "content" / "site.yml").read_text(encoding="utf-8")) or {}
    target = str(site.get("cv_pdf") or "").lstrip("/")
    if not target:
        sys.exit("Set cv_pdf in content/site.yml first.")
    page = OUT / "cv.html"
    if not page.exists():
        sys.exit("Run python build.py first.")
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome or Chromium is needed to make the PDF.")

    pdf = OUT / target
    pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([
            chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer", "--print-to-pdf-no-header",
            "--run-all-compositor-stages-before-draw", "--virtual-time-budget=8000",
            f"--print-to-pdf={pdf}", page.as_uri(),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not pdf.exists() or pdf.stat().st_size < 5000:
        sys.exit("The PDF was not created.")
    print(f"Made {pdf.relative_to(ROOT)} ({pdf.stat().st_size // 1024} KB)")
    if args.save:
        copy = ROOT / target
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(pdf, copy)
        print(f"Saved a copy as {target}")


if __name__ == "__main__":
    main()
