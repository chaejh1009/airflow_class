import csv
import json
from pathlib import Path

def read_orders(path="data/cafe_orders.csv"):
    # [문제 1 · 한 단어] with 구역 안에서 파일을 가리킬 이름이다.
    with open(path, encoding="utf-8-sig", newline="") as file:
        # [문제 2 · 한 줄] 행별 사전을 리스트로 모아 반환한다.
        # 예시: return list(csv.DictReader(stream))
        return list(csv.DictReader(file))

def paid_orders(rows):
    result = []
    for row in rows:
        # [문제 3 · 여러 줄] paid인 행만 result에 추가한다. (2줄)
        # 예시: if item["color"] == "blue":
        #           selected.append(item)
        if row["status"] == "paid":
            result.append(row)

    # [문제 4 · 한 단어] 선택한 주문을 모아 둔 리스트를 반환한다.
    return result

def summarize(rows):
    quantity = 0
    revenue = 0
    for row in rows:
        # [문제 5 · 여러 줄] 수량과 단가 문자열을 각각 정수로 바꾼다. (2줄)
        # 예시: units = int(item["units"])
        #       cost = int(item["cost"])
        count = int(row["quantity"])
        price = int(row["unit_price"])

        # [문제 6 · 한 줄] 이번 주문의 수량을 전체 수량에 더한다.
        # 예시: total_units += units
        quantity += count

        # [문제 7 · 한 단어] 정수로 바꾼 이번 주문의 단가를 곱한다.
        revenue += count * price
    return {"order_count": len(rows), "quantity": quantity, "revenue": revenue}

def save_json(value, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target)