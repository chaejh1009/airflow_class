from orders import read_orders
from reports import build_report
import json
import requests

def first_attempt(try_number):
    return try_number == 1

def make_daily_report(report_date, input_path="data/bakery_orders.csv", min_revenue=10000):
    return build_report(read_orders(input_path), report_date, min_revenue)

def attempt_report(report_date, simulate_failure, try_number, always_fail=False):
    # [1-H1 · 여러 줄] 지속 오류 또는 일시 오류의 첫 시도에서 실패시킨다. (2줄)
    # 예시: if enabled and count == 1:
    #           raise RuntimeError("try again")
    if always_fail or (simulate_failure and first_attempt(try_number)):
        raise RuntimeError("temporary order error.")

    return make_daily_report(report_date)

def notice_text(dag_id, task_id):
    return dag_id + "/" + task_id + " failed"

def failure_notice(context):
    ti = context["task_instance"]
    payload = {
        # [2-H1 · 여러 줄] 작업 이름, 실행 ID, 오류 문자열을 담는다. (3줄)
        # 예시: "text": label(project, step),
        #       "run_id": current_run,
        #       "error": str(error),
        "text": notice_text(ti.dag_id, ti.task_id),
        "run_id": ti.run_id,
        "error": str(context.get("exception", "unknown error")),
        "callback_test" : "콜백함수 테스트용메시지",
    }
    print("콜백함수에 실행할 내용을 또 추가했습니다.")
    print("FAILURE_NOTICE " + json.dumps(payload, ensure_ascii=False))
    return payload

# 콜백함수를 하나 더 만들어서, alert쪽에서 교체해서 써 보세요. 디스코드로 위의 payload를 전달해야 합니다.
def discord_failure_notice(context):
    # 기존 콜백을 호출해 실패 정보를 로그에 남기고, 전송할 payload를 받는다.
    payload = failure_notice(context)

    # 따옴표 안에 Discord 웹훅 URL을 직접 입력한다.
    webhook_url = ""
    if not webhook_url:
        raise ValueError("Discord 웹훅 URL을 입력해 주세요.")

    # payload를 JSON 문자열로 바꾸고, Discord 메시지 본문인 content에 담아 보낸다.
    response = requests.post(
        webhook_url,
        json={"content": json.dumps(payload, ensure_ascii=False)},
        timeout=10,
    )
    # HTTP 오류가 발생하면 예외를 발생시켜 콜백 로그에서 전송 실패를 확인한다.
    response.raise_for_status()
    return payload

# bakery_book_alert.py에서 discord_failure_notice를 import하고,
# on_failure_callback=discord_failure_notice로 교체한다. 함수 뒤에 ()를 붙이지 않는다.

def choose_report_task(report):
    if report["order_count"] > 0:
        return "write_report"
    return "no_orders"

def finish_payload(report_date):
    return {"report_date": report_date, "status": "finished"}

def can_deliver(report):
    # report의 주문count값과 target met(최소매출목표) 를 기반으로 참 거짓을 판단합니다.
    return report["order_count"] > 0 and report["target_met"]

def dag_name(store):
    return store + "_book_daily"