import csv


def read_first_order(path):
    # [문제 1-1 · 여러 줄] path를 열고 행별 사전을 rows에 모은다. (2줄)
    # 예시: with open("data/cafe_orders.csv", encoding="utf-8-sig", newline="") as source:
    #           sample = list(csv.DictReader(source))
    with open("data/bakery_orders.csv", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    # [문제 1-2 · 한 단어] 첫 원소의 인덱스다.
    return rows[0]

def read_bakery_orders(path="data/bakery_orders.csv"):
    # [문제 2-1 · 여러 줄] 파일을 열고 행별 사전 리스트를 반환한다. (2줄)
    # 예시: with open("data/cafe_orders.csv", encoding="utf-8-sig", newline="") as source:
    #           return list(csv.DictReader(source))
    with open("data/bakery_orders.csv", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))

def is_paid_order(row):
    # [문제 3-1 · 한 줄] 결제 상태의 비교 결과를 반환한다.
    # 예시: return row["menu"] == "tea"
    return row["status"] == "paid"

# 취소한게 몇 개이고 어떤건지 집계해보세요.
def select_paid_orders(rows):
    selected = []
    for row in rows:
        # [문제 4-1 · 여러 줄] 앞에서 만든 판단 함수가 True인 주문만 담는다. (2줄)
        # 예시: if row["menu"] == "tea":
        #           drinks.append(row)
        if row["status"] == "paid":
            selected.append(row)
    # [문제 4-2 · 한 단어] 선택한 주문을 담은 새 리스트다.
    return selected

def order_amount(row):
    # [문제 5-1 · 여러 줄] 수량과 단가를 각각 정수 count, price로 바꾼다. (2줄)
    # 예시: cups = int(sample["quantity"])
    #       won = int(sample["unit_price"])
    count = int(row["quantity"])
    price = int(row["unit_price"])

    # [문제 5-2 · 한 줄] 두 정수의 곱을 반환한다.
    # 예시: return cups * won
    return count * price

def summarize_bakery(rows):
    selected = select_paid_orders(rows)
    quantity = 0
    revenue = 0
    for row in selected:
        # [문제 6-1 · 여러 줄] 결제 주문의 수량과 금액을 누적한다. (2줄)
        # 예시: cups += int(sample["quantity"])
        #       won += order_amount(sample)
        quantity += int(row["quantity"])
        revenue += order_amount(row)

    # [문제 6-2 · 한 단어] 전체 rows가 아닌 결제 목록의 길이를 센다.
    return {"order_count": len(selected), "quantity": quantity, "revenue": revenue}