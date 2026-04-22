from __future__ import annotations

import json
import re
from pathlib import Path


def _clean_docs_root(docs_dir: Path) -> None:
        # Remove previously generated root-level year endpoints (e.g., docs/2026, docs/2026.json)
        # because the desired public path is now /api/{year}.
        year_file_re = re.compile(r"^\d{4}(?:\.json)?$")
        for child in docs_dir.iterdir():
                if not child.is_file():
                        continue
                if year_file_re.match(child.name) or child.name in {"index.json"}:
                        child.unlink(missing_ok=True)


def build_pages(data_dir: Path, docs_dir: Path) -> int:
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / ".nojekyll").write_text("", encoding="utf-8")

        _clean_docs_root(docs_dir)

        api_dir = docs_dir / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        years: list[int] = []

        for path in sorted(data_dir.glob("*.json")):
                try:
                        year = int(path.stem)
                except ValueError:
                        continue

                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict) or payload.get("year") != year:
                        raise SystemExit(f"Invalid payload: {path}")

                serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

                # Public endpoints:
                # - /api/2026
                # - /api/2026.json
                (api_dir / f"{year}").write_text(serialized, encoding="utf-8")
                (api_dir / f"{year}.json").write_text(serialized, encoding="utf-8")
                years.append(year)

        # Index of available years
        (api_dir / "index.json").write_text(
                json.dumps({"years": years}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
        )

        # Root documentation page
        docs_dir.joinpath("index.html").write_text(
                """<!doctype html>
<html lang=\"id\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Hari Libur API</title>
        <style>
            body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial;max-width:860px;margin:40px auto;padding:0 16px;line-height:1.45}
            code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,\"Liberation Mono\",\"Courier New\",monospace}
            pre{background:#f6f8fa;padding:12px;border-radius:8px;overflow:auto}
            a{color:#0969da;text-decoration:none}
            a:hover{text-decoration:underline}
            h1{margin:0 0 8px}
            .muted{color:#57606a}
        </style>
    </head>
    <body>
        <h1>Hari Libur API</h1>
        <p class=\"muted\">Static JSON API via GitHub Pages.</p>

        <h2>Endpoint</h2>
        <ul>
            <li><code>/api/{tahun}</code> (JSON)</li>
            <li><code>/api/{tahun}.json</code> (JSON)</li>
            <li><code>/api/index.json</code> (daftar tahun tersedia)</li>
        </ul>

        <h2>Contoh</h2>
        <pre><code>GET /api/2026</code></pre>

        <h2>Format respons</h2>
        <pre><code>{
    \"year\": 2026,
    \"source\": \"https://kalenderku.id/2026\",
    \"scraped_at\": \"2026-04-22T03:37:56.841805+00:00\",
    \"holidays\": [
        {
            \"date\": \"2026-01-16\",
            \"name\": \"Isra Mikraj Nabi Muhammad SAW\",
            \"type\": \"Libur Nasional\",
            \"holiday_type\": \"libur\"
        }
    ]
}</code></pre>
    </body>
</html>
""",
                encoding="utf-8",
        )

        return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/holidays"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()

    return build_pages(args.data_dir, args.docs_dir)


if __name__ == "__main__":
    raise SystemExit(main())
