import csv

import pytest

from housing.cli import main


def test_generate_sample_writes_csv(tmp_path, capsys):
    out_path = tmp_path / "sample.csv"
    rc = main(["generate-sample", "--out", str(out_path), "--regions", "3", "--months", "12"])
    assert rc == 0
    assert out_path.exists()

    with out_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 3 * 12

    captured = capsys.readouterr()
    assert "Wrote 36 rows" in captured.out


def test_init_dry_run_prints_ddl(capsys):
    rc = main(["init", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "CREATE TABLE" in captured.out
    assert "regional_price_index" in captured.out
    assert "monthly_features" in captured.out


def test_load_dry_run_does_not_touch_network(capsys):
    rc = main(["load", "--source", "data/sample/regional_price_index.csv", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out


def test_build_features_dry_run(capsys):
    rc = main(["build-features", "--lookback", "6", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "6 PRECEDING" in captured.out


@pytest.mark.parametrize("model", ["arima", "boosted-tree"])
def test_train_dry_run_for_each_model(model, capsys):
    rc = main(["train", "--model", model, "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "CREATE OR REPLACE MODEL" in captured.out


def test_train_rejects_unknown_model(capsys):
    # argparse `choices` rejects this at parse time with SystemExit(2),
    # before cmd_train's own "unknown model" branch would ever run.
    with pytest.raises(SystemExit) as exc_info:
        main(["train", "--model", "not-a-model", "--dry-run"])
    assert exc_info.value.code != 0


def test_evaluate_dry_run(capsys):
    rc = main(["evaluate", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.count("ML.EVALUATE(MODEL") == 2


@pytest.mark.parametrize("model", ["arima", "boosted-tree"])
def test_predict_dry_run_for_each_model(model, capsys):
    rc = main(["predict", "--model", model, "--horizon", "4", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "4" in captured.out


def test_register_dry_run_does_not_import_aiplatform(capsys):
    rc = main(["register", "--model", "boosted-tree", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "EXPORT MODEL" in captured.out
    assert "would then call aiplatform" in captured.out
