import pendulum
from airflow.sdk import DAG, Param, Variable
from airflow.providers.standard.operators.python import PythonOperator
from book_reporting import make_report


def report_for_date(report_date):
    # [5-H3 · 여러 줄] Variable을 정수로 읽고 그 기준으로 보고서를 만든다. (2줄)
    # 예시: limit = int(Variable.get("sample_limit", default="5000"))
    #       result = calculate(day, min_revenue=limit)
    threshold = int(Variable.get("bakery_min_revenue", default="10000"))
    report = make_report(report_date, min_revenue=threshold)
    print(report)
    return report


with DAG(
    dag_id="bakery_book_operator", schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"), catchup=False,
    max_active_runs=1, tags=["bakery", "book", "day05"],
    params={"report_date": Param("2026-10-05", type="string",
                                enum=["2026-10-05", "2026-10-06", "2026-10-07"])},
):
    PythonOperator(
        task_id="make_report", python_callable=report_for_date,
        op_kwargs={"report_date":"{{ params.report_date }}"},
    )