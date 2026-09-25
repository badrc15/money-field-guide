"""Create static market and news snapshots for the GitHub Pages build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import news_data, scout_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    scout = scout_data()
    news = news_data()
    news["message"] = "Fresh publisher RSS headlines, refreshed about hourly by GitHub Actions."

    for name, payload in (("scout", scout), ("news", news)):
        destination = args.output_dir / f"{name}.json"
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
