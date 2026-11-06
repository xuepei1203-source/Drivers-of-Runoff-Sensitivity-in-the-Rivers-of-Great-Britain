"""Figure 4: annual GAM variable importance based on PDP ranges.

Run from the project root in Jupyter:
    %run scripts/figure_04_annual_importance.py

Optional:
    %run scripts/figure_04_annual_importance.py --data "data/Catchments ID.xlsx"
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import ROOT, FEATURES, LABELS, TARGETS, load_annual, prepare, fit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path,
        default=ROOT / "data" / "Catchments ID.xlsx",
        help="Annual catchment workbook (default: data/Catchments ID.xlsx)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "figures",
        help="Output directory (default: figures/)",
    )
    args = parser.parse_args()

    if not args.data.is_file():
        parser.error(f"Annual workbook not found: {args.data}")

    args.output.mkdir(parents=True, exist_ok=True)
    df = load_annual(args.data)
    print(f"Loaded annual data: {args.data} ({len(df)} rows)", flush=True)

    for i, (metric, target) in enumerate(TARGETS.items()):
        x, y, _ = prepare(df, target)
        print(f"Fitting {metric}: {len(y)} catchments", flush=True)
        gam = fit(x, y)

        # Original Figure 4 definition: max(PDP) - min(PDP) for each predictor.
        strength = np.array([
            float(np.ptp(gam.partial_dependence(
                term=j, X=gam.generate_X_grid(term=j)
            )))
            for j in range(14)
        ])
        order = np.argsort(strength)[::-1]

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.barh(np.arange(14), strength[order])
        ax.set_yticks(np.arange(14), [LABELS[j] for j in order])
        ax.invert_yaxis()
        ax.set_xlabel("Influence Strength")
        ax.grid(axis="x", linestyle="--", alpha=0.7)
        fig.text(
            0.98, 0.02, "abc"[i], fontsize=18,
            fontweight="bold", ha="right"
        )
        fig.tight_layout()

        dest = args.output / f"figure_04_{metric}.png"
        fig.savefig(dest, dpi=300)
        plt.close(fig)
        print(f"Saved {dest}", flush=True)


if __name__ == "__main__":
    main()
