import pendulum
from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from book_operations import make_daily_report, choose_report_task, finish_payload
from orders import save_json


def read_day(**context):
    return make_daily_report(context["params"]["report_date"])


def pick_path(**context):
    return choose_report_task(context["ti"].xcom_pull(task_ids="read_report"))


def write_report(**context):
    report = context["ti"].xcom_pull(task_ids="read_report")
    return save_json(report, "outputs/book/day06/join/" + report["report_date"] + ".json")


def no_orders(**context):
    return {"report_date": context["params"]["report_date"], "status": "no_orders"}


def finish(**context):
    result = finish_payload(context["params"]["report_date"])
    print(result)
    return result


with DAG("bakery_book_join", schedule=None, catchup=False,
         start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
         params={"report_date": Param("2026-10-05", type="string")}) as dag:
    read = PythonOperator(task_id="read_report", python_callable=read_day)
    choose = BranchPythonOperator(task_id="choose", python_callable=pick_path)
    write = PythonOperator(task_id="write_report", python_callable=write_report)
    empty = PythonOperator(task_id="no_orders", python_callable=no_orders)
    joined = PythonOperator(task_id="finish", python_callable=finish,
                            trigger_rule="none_failed_min_one_success")
    read >> choose >> [write, empty]
    # [4-H2 · 한 줄] 두 분기 모두 finish의 상위 작업으로 연결한다.
    # 예시: [left, right] >> merge
    [write, empty] >> joined