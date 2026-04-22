from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

MONTHS_ID = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


@dataclass(frozen=True)
class Holiday:
    date: str  # ISO yyyy-mm-dd
    name: str
    type: str
    holiday_type: str  # 'libur' | 'cuti'


def _normalize_holiday_type(jenis: str) -> str:
    j = (jenis or "").strip().lower()
    if "cuti" in j:
        return "cuti"
    return "libur"


def _fetch(url: str) -> str:
    headers = {
        "User-Agent": "hari-libur-api/0.1 (+https://github.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    with httpx.Client(timeout=30, headers=headers, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text


def _find_holidays_ul(soup: BeautifulSoup, year: int):
    h2_text = f"Daftar Hari Libur Tahun {year}"
    h2 = soup.find(lambda tag: tag.name == "h2" and tag.get_text(" ", strip=True) == h2_text)
    if h2 is None:
        return None

    # The list of holidays is rendered as:
    # <ul class="columns-1 lg:columns-2"> <li> ... <span class="sr-only">Kamis 1 Januari - ... - Libur Nasional</span>
    for ul in h2.find_all_next("ul"):
        ul_classes = ul.get("class", [])
        if not isinstance(ul_classes, list):
            continue
        if "columns-1" not in ul_classes:
            continue

        first_sr_only = ul.find("span", class_="sr-only")
        if first_sr_only and " - " in first_sr_only.get_text(" ", strip=True):
            return ul

    return None


_date_re = re.compile(r"(\d{1,2})\s+([A-Za-z]+)")


def _parse_date(year: int, tanggal_text: str) -> str:
    # Examples: "Kamis 1 Januari" or "Selasa 25 Agustus"
    m = _date_re.search(tanggal_text)
    if not m:
        raise ValueError(f"Cannot parse tanggal: {tanggal_text!r}")

    day = int(m.group(1))
    month_name = m.group(2).strip().lower()
    if month_name not in MONTHS_ID:
        raise ValueError(f"Unknown month name: {month_name!r} from {tanggal_text!r}")

    month = MONTHS_ID[month_name]
    return f"{year:04d}-{month:02d}-{day:02d}"


def _iter_rows(ul) -> Iterable[tuple[str, str, str]]:
    for li in ul.find_all("li", recursive=False):
        sr = li.find("span", class_="sr-only")
        if sr is None:
            continue

        # Example:
        # "Kamis 1 Januari - Tahun Baru Masehi 2026 - Libur Nasional"
        text = sr.get_text(" ", strip=True)
        parts = [p.strip() for p in text.split(" - ") if p.strip()]
        if len(parts) < 3:
            continue

        tanggal = parts[0]
        nama = parts[1]
        jenis = parts[-1]
        yield tanggal, nama, jenis


def scrape_year(year: int) -> dict:
    url = f"https://kalenderku.id/{year}"
    html = _fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    ul = _find_holidays_ul(soup, year)
    if ul is None:
        raise RuntimeError(
            f"Tidak menemukan section 'Daftar Hari Libur Tahun {year}'. Struktur HTML mungkin berubah."
        )

    holidays: list[Holiday] = []
    for tanggal_text, name, typ in _iter_rows(ul):
        iso_date = _parse_date(year, tanggal_text)
        holidays.append(
            Holiday(
                date=iso_date,
                name=name,
                type=typ,
                holiday_type=_normalize_holiday_type(typ),
            )
        )

    holidays_sorted = sorted(holidays, key=lambda h: (h.date, h.type, h.name))

    return {
        "year": year,
        "source": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "holidays": [h.__dict__ for h in holidays_sorted],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--end-year", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--years-back", type=int, default=1)
    args = parser.parse_args()

    if args.year is not None:
        if args.out is None:
            raise SystemExit("--out wajib jika memakai --year")
        payload = scrape_year(args.year)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0

    if args.out_dir is None:
        raise SystemExit("Pakai salah satu: (--year dan --out) atau (--out-dir dengan --years-back/--end-year)")

    if args.years_back < 1:
        raise SystemExit("--years-back minimal 1")

    start_year = args.end_year - args.years_back + 1
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for y in range(start_year, args.end_year + 1):
        payload = scrape_year(y)
        out_path = args.out_dir / f"{y}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
