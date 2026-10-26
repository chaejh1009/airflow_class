import pendulum
from airflow.sdk import Param, dag, get_current_context, task
from orders import read_orders
from workflow_day05 import select_day


@dag(dag_id="bakery_day05_select", schedule=None,
     start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
     catchup=False, max_active_runs=1, tags=["bakery", "day05"],
     params={"report_date": Param("2026-10-05", type="string",
                                  enum=["2026-10-05", "2026-10-06", "2026-10-07"]),
             "duplicate_first": Param(False, type="boolean")})
def bakery_day05_select():
    @task
    def read_source():
        rows = read_orders("data/bakery_orders.csv")
        if get_current_context()["params"]["duplicate_first"]:
            rows.append(rows[0].copy())
        return rows

    @task
    def select(rows):
        report_date = get_current_context()["params"]["report_date"]
        return select_day(rows, report_date)

    @task
    def evidence(packet):
        print(packet["report_date"], packet["source_count"],
              packet["selected_count"], packet["rejected_count"])
        print(packet["order_ids"])
        return packet["order_ids"]

    # [어려운 문제 2-C · 한 줄] 읽기 → 선택 → 증거 출력 순서로 연결한다.
    # 예시: show(convert(load()))
    evidence(select(read_source()))


bakery_day05_select()