def meets_target(revenue, limit_text):
    # [문제 1-1 · 한 줄] 기준 문자열을 정수 limit으로 바꾼다.
    # 예시: minimum = int("5000")
    limit = int(limit_text)
    # [문제 1-2 · 한 단어] 기준과 같아도 달성이다.
    return revenue >= limit

def show_targets(limit_text):
    # [문제 2-1 · 여러 줄] 첫 매출 14000과 둘째 매출 8500을 각각 비교해 출력한다. (2줄)
    # 예시: print(4500, meets_target(4500, limit_text))
    print(14000, meets_target(14000, limit_text))
    print(8500, meets_target(8500, limit_text))

def date_matches(row, report_date):
    # [문제 3-1 · 한 줄] 주문 날짜와 요청 날짜가 같은지 반환한다.
    # 예시: return item["day"] == wanted
    return row["order_date"] == report_date

def summary_card(report_date, totals):
    return {
        "report_date": report_date,  # [5-E1 · 한 단어] 입력받은 날짜
        "order_count": totals["order_count"],
        "quantity": totals["quantity"],
        # [5-E2 · 한 줄] totals의 매출을 revenue 항목에 담는다.
        # 예시: "quantity": totals["quantity"],
        "revenue": totals["revenue"],
    }