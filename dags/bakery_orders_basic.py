import pendulum
from airflow.sdk import dag, task
from orders import paid_orders, read_orders, summarize


@dag(dag_id="bakery_orders_basic", schedule=None,
     start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
     catchup=False, max_active_runs=1, tags=["bakery", "beginner"])
def bakery_orders_basic():
    @task
    def read():
        # [문제 7-1 · 한 단어] 문제 데이터 파일 이름을 채운다.
        return read_orders("data/bakery_orders.csv")

    @task
    def keep_paid(rows):
        # [문제 7-2 · 한 줄] 결제 주문 목록을 반환한다.
        # 예시: return read_orders(path)
        return paid_orders(rows)

    # [문제 7-3 · 여러 줄] total Task를 정의하고 받은 rows의 합계를 반환한다. (3줄)
    # 예시: @task
    #       def load():
    #           return read_orders()
    @task
    def total(rows):
        return summarize(rows)

    # [문제 7-4 · 한 줄] 읽기→선택→합산 반환값을 연결한다.
    # 예시: keep_paid(read())
    total(keep_paid(read()))


bakery_orders_basic()