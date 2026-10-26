import pendulum
from airflow.sdk import DAG, Param, Variable, get_current_context
from airflow.providers.standard.operators.python import PythonOperator
from book_reporting import read_report, write_report


def produce_explicit():
    context = get_current_context()
    threshold = int(Variable.get("bakery_min_revenue", default="10000"))
    path = write_report(context["params"]["report_date"], context["run_id"], threshold)
    # [7-H1 · 한 줄] 경로를 report_path 키로 보낸다.
    # 예시: context["ti"].xcom_push(key="result_id", value=result_id)
    context["ti"].xcom_push(key="report_path", value=path)


def consume_explicit():
    # [7-H2 · 한 줄] make_report Task의 report_path를 받아 path에 저장한다.
    # 예시: value = get_current_context()["ti"].xcom_pull(task_ids="producer", key="result_id")

    # context = get_current_context()
    # path = context["ti"].xcom_pull(task_ids="make_report", key="report_path")

    path = get_current_context()["ti"].xcom_pull(task_ids="make_report", key="report_path")

    report = read_report(path)
    print(report["report_date"], report["revenue"])
    return report


def produce_return():
    context = get_current_context()
    threshold = int(Variable.get("bakery_min_revenue", default="10000"))
    # [7-H3 · 한 줄] 같은 파일 저장 함수의 경로를 반환하여 자동 XCom에 맡긴다.
    # 예시: return persist(day, execution_id, limit)
    return write_report(context["params"]["report_date"], context["run_id"], threshold)


def consume_return():
    # [7-H4 · 한 줄] 자동 반환 키를 사용해 path를 읽는다.
    # 예시: value = get_current_context()["ti"].xcom_pull(task_ids="producer")
    path = get_current_context()["ti"].xcom_pull(task_ids="make_report")
    report = read_report(path)
    print(report["report_date"], report["revenue"])
    return report


with DAG(
    dag_id="bakery_book_xcom_explicit", schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"), catchup=False,
    max_active_runs=1, tags=["bakery", "book", "day05"],
    params={"report_date": Param("2026-10-05", type="string",
                                enum=["2026-10-05", "2026-10-06", "2026-10-07"])},
):
    make = PythonOperator(task_id="make_report", python_callable=produce_explicit)
    read = PythonOperator(task_id="read_report", python_callable=consume_explicit)
    make >> read


with DAG(
    dag_id="bakery_book_xcom_return", schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"), catchup=False,
    max_active_runs=1, tags=["bakery", "book", "day05"],
    params={"report_date": Param("2026-10-05", type="string",
                                enum=["2026-10-05", "2026-10-06", "2026-10-07"])},
):
    make = PythonOperator(task_id="make_report", python_callable=produce_return)
    read = PythonOperator(task_id="read_report", python_callable=consume_return)
    make >> read
