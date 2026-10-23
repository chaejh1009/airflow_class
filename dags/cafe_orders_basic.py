import pendulum
from airflow.sdk import dag, task
from orders import paid_orders, read_orders, save_json, summarize


@dag(dag_id="cafe_orders_basic", schedule=None,
     start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
     catchup=False, max_active_runs=1, tags=["cafe", "beginner"])
def cafe_orders_basic():
    @task
    def read():
        return read_orders()

    @task
    def keep_paid(rows):
        # [문제 8 · 한 줄] 받은 rows를 결제 선택 함수에 전달하고 결과를 반환한다.
        # 예시: return choose_items(items)
        return paid_orders(rows)

    @task
    def total(rows):
        # [문제 9 · 한 단어] 주문 건수·수량·매출을 합산하는 함수 이름이다.
        return summarize(rows)

    @task
    def save(summary):
        path = save_json(summary, "outputs/day04-summary.json")
        print(summary)
        return path

    # [문제 10 · 한 줄] 읽기→선택→합산→저장 순서로 반환값을 연결한다.
    # 예시: show(double(add_one(2)))
    save(total(keep_paid(read())))

cafe_orders_basic()