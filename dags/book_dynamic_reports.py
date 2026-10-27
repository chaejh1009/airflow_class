import pendulum
from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.python import PythonOperator
from book_operations import dag_name, make_daily_report
from orders import save_json

STORES = [
    {"store": "cafe", "input_path": "data/cafe_orders.csv", "min_revenue": 15000, "default_date": "2026-10-01"},
    {"store": "bakery", "input_path": "data/bakery_orders.csv", "min_revenue": 10000, "default_date": "2026-10-05"},
]


def run_store(store, input_path, min_revenue, **context):
    report_date = context["dag_run"].conf.get("report_date", context["params"]["report_date"])
    # [6-H1 · 한 줄] 이 매장 입력 경로·기준과 실행 날짜로 보고서를 만든다.
    # 예시: result = calculate(day, source, limit)
    report = make_daily_report(report_date, input_path, min_revenue)

    path = "outputs/book/day06/dynamic/" + store + "/" + report_date + ".json"
    print(report)
    return save_json(report, path)


def create_store_dag(spec):
    with DAG(dag_name(spec["store"]), schedule=None, catchup=False,
             start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
             params={"report_date": Param(spec["default_date"], type="string")}) as generated:
        PythonOperator(task_id="report", python_callable=run_store,
                       # [6-H2 · 여러 줄] 세 함수 인자 이름에 현재 설정의 값을 연결한다. (2줄)
                       # 예시: op_kwargs={"region": setting["region"],
                       #                  "source": setting["source"]}
                       op_kwargs={"store": spec["store"],
                                  "input_path": spec["input_path"],
                                  "min_revenue": spec["min_revenue"]}
                                    )
    return generated


for spec in STORES:
    # [6-H3 · 한 줄] 현재 설정으로 만든 DAG를 그 매장 이름에 등록한다.
    # 예시: globals()[object_name(item)] = build_object(item)
    globals()[dag_name(spec["store"])] = create_store_dag(spec)