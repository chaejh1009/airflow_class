import pendulum
from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from book_operations import make_daily_report, choose_report_task
from orders import save_json


def read_day(**context):
    return make_daily_report(context["params"]["report_date"])


def pick_path(**context):
    # [3-H1 · 한 줄] read_report의 XCom을 선택 함수에 넘긴다.
    # 예시: return decide(context["ti"].xcom_pull(task_ids="load"))
    return choose_report_task(context["ti"].xcom_pull(task_ids="read_report"))


def write_report(**context):
    report = context["ti"].xcom_pull(task_ids="read_report")
    return save_json(report, "outputs/book/day06/branch/" + report["report_date"] + ".json")


def no_orders(**context):
    date = context["params"]["report_date"]
    print({"report_date": date, "status": "no_orders"})
    return {"report_date": date, "status": "no_orders"}


with DAG("bakery_book_branch", schedule=None, catchup=False,
         start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
         params={"report_date": Param("2026-10-05", type="string")}) as dag:
    read = PythonOperator(task_id="read_report", python_callable=read_day)
    choose = BranchPythonOperator(task_id="choose", python_callable=pick_path)
    write = PythonOperator(task_id="write_report", python_callable=write_report)
    empty = PythonOperator(task_id="no_orders", python_callable=no_orders)
    # [3-H2 · 한 줄] 읽기 뒤 선택, 선택 뒤 두 후보 작업을 연결한다.
    # 예시: source >> route >> [left, right]
    read >> choose >> [write, empty]