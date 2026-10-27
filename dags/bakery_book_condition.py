import pendulum
from airflow.sdk import DAG, Param
from airflow.exceptions import AirflowSkipException
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from book_operations import make_daily_report, can_deliver
from orders import save_json


def check_delivery(**context):
    report = make_daily_report(context["params"]["report_date"])
    # [5-H1 · 여러 줄] 전달 조건이 거짓이면 작업을 skip한다. (2줄)
    # 예시: if not ready:
    #           raise AirflowSkipException("not ready")
    if not can_deliver(report):
        raise AirflowSkipException("delivery condition not met")

    return report


def deliver(**context):
    report = context["ti"].xcom_pull(task_ids="check_delivery")
    return save_json(report, "outputs/book/day06/delivery/" + report["report_date"] + ".json")


with DAG("bakery_book_condition", schedule=None, catchup=False,
         start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
         params={"report_date": Param("2026-10-05", type="string")}, tags=["day6", "bakery"]) as dag:
    check = PythonOperator(task_id="check_delivery", python_callable=check_delivery)
    send = PythonOperator(task_id="deliver", python_callable=deliver)
    observed = EmptyOperator(task_id="observed", trigger_rule="none_failed")
    # [5-H3 · 한 줄] 조건 확인 → 전달 → 관찰 순서를 연결한다.
    # 예시: test >> action >> end
    check >> send >> observed