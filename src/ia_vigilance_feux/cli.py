from __future__ import annotations

import argparse
from pathlib import Path

from ia_vigilance_feux.backtest import run_temporal_backtest, write_backtest_outputs
from ia_vigilance_feux.modeling import load_feature_table, save_bundle


def main() -> None:
    parser = argparse.ArgumentParser(prog="ia-feux")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="Entrainer et backtester sur des donnees historiques reelles")
    train.add_argument("--features", required=True, help="CSV de features historiques reelles")
    train.add_argument("--train-end-year", type=int, required=True)
    train.add_argument("--test-year", type=int, required=True)
    train.add_argument("--version", default="model_v001")
    train.add_argument("--model-dir", default="models")
    train.add_argument("--output-dir", default="data/backtests/latest")

    args = parser.parse_args()
    if args.command == "train":
        df = load_feature_table(args.features)
        result = run_temporal_backtest(
            df,
            train_end_year=args.train_end_year,
            test_year=args.test_year,
            version=args.version,
        )
        model_path = save_bundle(result.model, args.model_dir)
        write_backtest_outputs(result, args.output_dir)
        latest_dir = Path("data/model_registry")
        latest_dir.mkdir(parents=True, exist_ok=True)
        (latest_dir / "current_metrics.json").write_text(
            Path(args.output_dir, "metrics.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
        print(f"Modele sauvegarde: {model_path}")
        print(f"Resultats backtest: {args.output_dir}")
