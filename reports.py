from orders import paid_orders, summarize

def filter_date(rows, report_date):
    # [쉬운 문제 1-1 · 한 줄] 선택한 행을 담을 빈 목록 result를 만든다.
    # 예시: matched = []
    result = []
    # [쉬운 문제 1-2 · 여러 줄] 각 행의 order_date가 요청 날짜와 같으면 추가한다. (3줄)
    # 예시: for item in items:
    #           if item["day"] == wanted:
    #               matched.append(item)
    for row in rows:
        if row["order_date"] == report_date:
            result.append(row)

    # [쉬운 문제 1-3 · 한 단어] 선택한 행을 담은 목록 이름이다.
    return result

def build_report(rows, report_date, min_revenue):
    # 날짜 선택과 결제 상태 필터를 적용한 뒤 기준과 결과를 함께 기록한다.
    # [5-H1 · 여러 줄] 날짜 선택→결제 완료 선택→집계 순서로 작성한다. (2줄)
    # 예시: selected = choose(items, wanted)
    #       total = calculate(accepted(selected))
    selected = filter_date(rows, report_date)
    summary = summarize(paid_orders(selected))

    return {
        "report_date": report_date,
        "order_count": summary["order_count"],
        "quantity": summary["quantity"],
        "revenue": summary["revenue"],
        "min_revenue": min_revenue,
        "target_met": summary["revenue"] >= min_revenue,
    }
