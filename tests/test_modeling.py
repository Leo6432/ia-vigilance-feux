from pathlib import Path

import pandas as pd
import pytest

from ia_vigilance_feux.modeling import load_feature_table


def test_load_feature_table_rejects_future_available_at(tmp_path: Path):
    path = tmp_path / "features.csv"
    pd.DataFrame(
        [
            {
                "department_code": "53",
                "target_date": "2025-08-15",
                "horizon": 2,
                "available_at": "2025-08-16T00:00:00",
                "label_level": 2,
                "tmax": 31.2,
            }
        ]
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="Data leakage"):
        load_feature_table(path)
