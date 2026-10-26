import pendulum
from airflow.sdk import Param, dag, get_current_context, task
from book_reporting import join_shop_reports, run_path
from orders import read_orders, paid_orders, summarize, save_json
from reports import filter_date


@dag(dag_id="bakery_book_taskflow", schedule=None,
     start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"), catchup=False,
     max_active_runs=1, tags=["cafe", "bakery", "book", "day05"],
     params={
         "cafe_date": Param("2026-10-01", type="string", enum=["2026-10-01", "2026-10-02"]),
         "bakery_date": Param("2026-10-05", type="string", enum=["2026-10-05", "2026-10-06"]),
     })
def bakery_book_taskflow():
    @task
    def read(source_path):
        return read_orders(source_path)

    @task
    def clean(rows, date_key):
        date = get_current_context()["params"][date_key]
        # [8-H1 · 한 줄] 날짜가 맞는 주문에서 결제 완료만 반환한다.
        # 예시: return accepted(select_day(items, wanted))
        return paid_orders(filter_date(rows, date))

    @task
    def summary(rows, date_key):
        # [8-H2 · 여러 줄] 집계 사전에 선택한 업무 날짜를 붙여 반환한다. (3줄)
        # 예시: result = calculate(items)
        #       result["day"] = config["day"]
        #       return result
        result = summarize(rows)
        result["report_date"] = get_current_context()["params"][date_key]
        print("서머라이즈된 결과물 : ", result)
        return result

    @task
    def join(cafe, bakery):
        return join_shop_reports(cafe, bakery)

    @task
    def save(report):
        print(report)
        return save_json(report, run_path(get_current_context()["run_id"], "combined.json"))

    cafe_rows = read.override(task_id="read_cafe")("data/cafe_orders.csv")
    bakery_rows = read.override(task_id="read_bakery")("data/bakery_orders.csv")
    # [8-H3 · 여러 줄] 매장별 read→clean→summary를 연결한 뒤 두 결과를 join→save한다. (5줄)
    # 예시: left_clean = clean.override(task_id="clean_left")(left_rows, "left_date")
    #       left = summary.override(task_id="summary_left")(left_clean, "left_date")
    #       save(join(left, right))
    cafe_clean = clean.override(task_id="clean_cafe")(cafe_rows, "cafe_date")
    bakery_clean = clean.override(task_id="clean_bakery")(bakery_rows, "bakery_date")
    cafe = summary.override(task_id="summary_cafe")(cafe_clean, "cafe_date")
    bakery = summary.override(task_id="summary_bakery")(bakery_clean, "bakery_date")
    save(join(cafe, bakery))

bakery_book_taskflow()