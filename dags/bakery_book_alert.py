from datetime import timedelta
import pendulum
from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.python import PythonOperator
from book_operations import attempt_report, failure_notice, discord_failure_notice


def read_day(**context):
    params = context["params"]
    return attempt_report(params["report_date"], False,
                          context["ti"].try_number, params["always_fail"])


with DAG("bakery_book_alert", schedule=None, catchup=False,
         start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
         params={"report_date": Param("2026-10-05", type="string"),
                 "always_fail": Param(False, type="boolean")}) as dag:
    read_report = PythonOperator(task_id="read_report", python_callable=read_day,
                                 retries=1, retry_delay=timedelta(seconds=5),
                                 on_failure_callback=discord_failure_notice)