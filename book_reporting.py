from orders import read_orders, save_json
from reports import build_report
from urllib.parse import quote
import json
from pathlib import Path

def make_report(report_date, source_path="data/bakery_orders.csv", min_revenue=10000):
    rows = read_orders(source_path)
    return build_report(rows, report_date, min_revenue)

def run_path(run_id, filename="report.json"):
    return "outputs/practice/book/day05/" + quote(run_id, safe="") + "/" + filename

def write_report(report_date, run_id, min_revenue=10000, source_path="data/bakery_orders.csv"):
    report = make_report(report_date, source_path, min_revenue)
    # [6-E1 · 한 줄] 보고서를 실행별 경로에 저장하고 경로를 반환한다.
    # 예시: return save_json(result, "outputs/sample.json")
    return save_json(report, run_path(run_id))

def read_report(path):
    # [7-E1 · 한 단어] JSON 문자열을 Python 사전으로 바꾸는 함수
    return json.loads(Path(path).read_text(encoding="utf-8"))

def join_shop_reports(cafe, bakery):
    return {
        "report_dates": {"cafe": cafe["report_date"], "bakery": bakery["report_date"]},
        "shops": {"cafe": cafe, "bakery": bakery},
        "total_revenue": cafe["revenue"] + bakery["revenue"],
    }