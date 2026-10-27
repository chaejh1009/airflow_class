from pathlib import Path

import pendulum
from airflow.sdk import DAG, Param
from airflow.exceptions import AirflowSkipException
from airflow.providers.standard.operators.python import PythonOperator

from bakery_ml import prepare_data, train_model, evaluate_model, approve_model, predict_active, save_json


def prepare_task(**context):
    prepared_path = prepare_data(context["params"]["source_path"], context["run_id"])
    if prepared_path is None:
        raise AirflowSkipException("dataset has not changed since the last decision")
    return prepared_path


def train_task(**context):
    return train_model(context["ti"].xcom_pull(task_ids="prepare"))


def evaluate_task(**context):
    candidate_path = context["ti"].xcom_pull(task_ids="train")
    return evaluate_model(candidate_path, context["params"]["max_mae"])


def approve_task(**context):
    metrics_path = context["ti"].xcom_pull(task_ids="evaluate")
    active_path = approve_model(metrics_path)
    if active_path is None:
        raise AirflowSkipException("model quality did not pass; active model is preserved")
    return active_path


def predict_task(**context):
    active_path = context["ti"].xcom_pull(task_ids="approve")
    metrics_path = context["ti"].xcom_pull(task_ids="evaluate")
    prediction = predict_active(active_path, context["params"]["expected_visitors"])
    return save_json(prediction, Path(metrics_path).parent / "prediction.json")


with DAG("bakery_book_ml", schedule="*/1 * * * *", catchup=False, max_active_runs=1,
         start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
         params={"source_path": Param("data/bakery_demand.csv", type="string"),
                 "max_mae": Param(3.0, type="number", minimum=0),
                 "expected_visitors": Param(90, type="number", minimum=0)}) as dag:
    prepare = PythonOperator(task_id="prepare", python_callable=prepare_task)
    train = PythonOperator(task_id="train", python_callable=train_task)
    evaluate = PythonOperator(task_id="evaluate", python_callable=evaluate_task)
    approve = PythonOperator(task_id="approve", python_callable=approve_task)
    predict = PythonOperator(task_id="predict", python_callable=predict_task)
    # [7-H3 · 한 줄] 데이터 준비 → 학습 → 평가 → 승인 → 예측 순서로 연결한다.
    # 예시: first >> second >> third
    prepare >> train >> evaluate >> approve >> predict
