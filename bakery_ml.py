import csv
import hashlib
import io
import json
import math
import os
import platform
import re
import shutil
from pathlib import Path

import joblib
from sklearn import __version__ as sklearn_version
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

def to_xy(rows):
    X = []
    y = []
    for row in rows:
        visitors = float(row["expected_visitors"])
        sold = float(row["sold_quantity"])
        if not math.isfinite(visitors) or not math.isfinite(sold) or visitors < 0 or sold < 0:
            raise ValueError("visitors and sold quantity must be finite non-negative numbers")
        # [7-E1 · 한 줄] 한 표본의 특징을 리스트로 감싸 X에 넣는다.
        # 예시: samples.append([value])
        X.append([visitors])
        # [7-E2 · 한 단어] 같은 행의 실제 판매량을 y에 추가한다.
        y.append(sold)
    return X, y

def train_model(prepared_path):
    path = Path(prepared_path).parent / "candidate.joblib"
    if path.exists():
        return str(path)
    prepared = read_json(prepared_path)
    # [7-H1 · 여러 줄] 회귀 모델 생성 → 학습용 X와 y로 학습한다. (2줄)
    # 예시: estimator = LinearRegression()
    #       estimator.fit(samples, targets)
    model = LinearRegression()
    model.fit(prepared["train"]["X"], prepared["train"]["y"])

    temporary = path.with_name(path.name + ".tmp")
    # [7-H2 · 한 줄] 학습된 모델을 임시 파일에 저장한다.
    # 예시: joblib.dump(result, file_path)
    joblib.dump(model, temporary)

    os.replace(temporary, path)
    return str(path)

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(data, path):
    path = Path(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return str(path)


def atomic_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    save_json(data, temporary)
    os.replace(temporary, path)
    return str(path)


def run_folder(run_id, output_root):
    label = re.sub(r"[^A-Za-z0-9._-]+", "_", run_id).strip("._-")[:60] or "run"
    suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:16]
    return Path(output_root) / "runs" / (label + "-" + suffix)


def runtime_versions():
    return {"python": platform.python_version(), "scikit_learn": sklearn_version,
            "joblib": joblib.__version__}


def prepare_data(source_path, run_id, output_root="outputs/book/day06/ml"):
    folder = run_folder(run_id, output_root)
    prepared_path = folder / "prepared.json"
    if prepared_path.exists():
        return str(prepared_path)
    source_bytes = Path(source_path).read_bytes()
    dataset_hash = hashlib.sha256(source_bytes).hexdigest()
    registry = Path(output_root) / "registry"
    attempted_path = registry / "attempted.json"
    if attempted_path.exists() and read_json(attempted_path)["dataset_hash"] == dataset_hash:
        return None
    rows = sorted(csv.DictReader(io.StringIO(source_bytes.decode("utf-8"))), key=lambda row: row["date"])
    if len(rows) < 8 or len({row["date"] for row in rows}) != len(rows):
        raise ValueError("Need at least 8 daily rows with different dates")
    train_rows, test_rows = rows[:-2], rows[-2:]
    train_X, train_y = to_xy(train_rows)
    test_X, test_y = to_xy(test_rows)
    prepared = {"run_id": run_id, "source_path": str(source_path), "dataset_hash": dataset_hash,
                "registry_path": str(registry), "feature": "expected_visitors", "target": "sold_quantity",
                "train": {"dates": [row["date"] for row in train_rows], "X": train_X, "y": train_y},
                "test": {"dates": [row["date"] for row in test_rows], "X": test_X, "y": test_y}}
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "source.csv").write_bytes(source_bytes)
    return atomic_json(prepared, prepared_path)


def passes_quality(mae, baseline_mae, max_mae, active_mae=None):
    return mae <= max_mae and mae < baseline_mae


def evaluate_model(candidate_path, max_mae=3.0):
    folder = Path(candidate_path).parent
    metrics_path = folder / "metrics.json"
    if metrics_path.exists():
        return str(metrics_path)
    if not math.isfinite(max_mae) or max_mae < 0:
        raise ValueError("max_mae must be a finite non-negative number")
    prepared = read_json(folder / "prepared.json")
    model = joblib.load(candidate_path)
    actual = prepared["test"]["y"]
    predicted = model.predict(prepared["test"]["X"]).tolist()
    train_y = prepared["train"]["y"]
    baseline = sum(train_y) / len(train_y)
    mae = float(mean_absolute_error(actual, predicted))
    baseline_mae = float(mean_absolute_error(actual, [baseline] * len(actual)))
    active_path = Path(prepared["registry_path"]) / "active.json"
    active = read_json(active_path) if active_path.exists() else None
    active_mae = None
    if active is not None:
        active_predictions = joblib.load(active["model_path"]).predict(prepared["test"]["X"])
        active_mae = float(mean_absolute_error(actual, active_predictions))
    metrics = {"run_id": prepared["run_id"], "dataset_hash": prepared["dataset_hash"],
               "registry_path": prepared["registry_path"], "mae": mae, "baseline_mae": baseline_mae,
               "active_mae": active_mae, "active_version": active["version"] if active else None,
               "max_mae": max_mae, "accepted": passes_quality(mae, baseline_mae, max_mae, active_mae),
               "train_rows": len(train_y), "test_rows": len(actual),
               "test_dates": prepared["test"]["dates"], "actual": actual, "predicted": predicted,
               "baseline_prediction": baseline, "runtime": runtime_versions()}
    return atomic_json(metrics, metrics_path)


def register_version(metrics, metrics_path):
    registry = Path(metrics["registry_path"])
    versions = registry / "models"
    versions.mkdir(parents=True, exist_ok=True)
    if "registered_version" not in metrics:
        numbers = [int(p.name[1:]) for p in versions.iterdir() if re.fullmatch(r"v[0-9]+", p.name)]
        metrics["registered_version"] = "v" + str(max(numbers, default=0) + 1)
        atomic_json(metrics, metrics_path)
    version = metrics["registered_version"]
    model_path = versions / version / "model.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if not model_path.exists():
        temporary = model_path.with_name("model.joblib.tmp")
        shutil.copyfile(Path(metrics_path).parent / "candidate.joblib", temporary)
        os.replace(temporary, model_path)
    active = {"version": version, "model_path": str(model_path),
              "dataset_hash": metrics["dataset_hash"], "run_id": metrics["run_id"],
              "metrics_path": str(metrics_path)}
    return atomic_json(active, registry / "active.json")


def approve_model(metrics_path):
    metrics = read_json(metrics_path)
    registry = Path(metrics["registry_path"])
    active_path = registry / "active.json"
    active = read_json(active_path) if active_path.exists() else None
    current_version = active["version"] if active else None
    already_active = (active is not None and active["dataset_hash"] == metrics["dataset_hash"]
                      and current_version == metrics.get("registered_version"))
    if current_version != metrics["active_version"] and not already_active:
        raise ValueError("stale candidate: active model changed after evaluation")
    attempt = {"dataset_hash": metrics["dataset_hash"], "run_id": metrics["run_id"],
               "status": "approved" if metrics["accepted"] else "rejected",
               "metrics_path": str(metrics_path)}
    if not metrics["accepted"]:
        atomic_json(attempt, registry / "attempted.json")
        return None
    if active is None or active["dataset_hash"] != metrics["dataset_hash"]:
        register_version(metrics, metrics_path)
    atomic_json(attempt, registry / "attempted.json")
    return str(active_path)


def predict_active(active_path, expected_visitors=90):
    expected_visitors = float(expected_visitors)
    if not math.isfinite(expected_visitors) or expected_visitors < 0:
        raise ValueError("expected_visitors must be a finite non-negative number")
    active = read_json(active_path)
    model = joblib.load(active["model_path"])
    prediction = float(model.predict([[expected_visitors]])[0])
    return {"version": active["version"], "model_path": active["model_path"],
            "expected_visitors": expected_visitors, "predicted_quantity": prediction}


def improves_active(mae, active_mae):
    # [8-E1 · 한 줄] 기존 모델이 없거나 새 MAE가 더 작으면 참이다.
    # 예시: return previous is None or current < previous
    return active_mae is None or mae < active_mae

def passes_quality(mae, baseline_mae, max_mae, active_mae=None):
    # [8-H1 · 여러 줄] 허용 오차 초과 또는 평균 예측보다 못하면 거절한다. (2줄)
    # 예시: if value > limit or value >= reference:
    #           return False
    if mae > max_mae or mae >= baseline_mae:
        return False

    # [8-H2 · 한 줄] 남은 후보는 현재 활성 모델보다 개선됐는지 확인한다.
    # 예시: return compare(current, previous)
    return improves_active(mae, active_mae)