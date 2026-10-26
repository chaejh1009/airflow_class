from reports import filter_date

def select_day(rows, report_date):
    selected = filter_date(rows, report_date)
    order_ids = []
    # [어려운 문제 2-A · 여러 줄] ID 목록을 만들고 중복을 거부한 뒤 새 ID를 추가한다. (6줄)
    # 예시: if code in seen:
    #           raise ValueError("duplicate code: " + code)
    #       seen.append(code)
    for row in selected:
        order_id = row["order_id"]
        if order_id in order_ids:
            raise ValueError("duplicate id: " + order_id)
        order_ids.append(row)

    return {
        "report_date": report_date,
        "source_count": len(rows),
        "selected_count": len(selected),
        # [어려운 문제 2-B · 한 줄] 전체 행 수에서 선택 행 수를 뺀 키·값을 작성한다.
        # 예시: "remaining": total - used,
        "rejected_count": len(rows) - len(selected),
        "order_ids": order_ids,
        "rows": selected,
    }