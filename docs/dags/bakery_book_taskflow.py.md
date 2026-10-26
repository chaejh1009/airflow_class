# dags/bakery_book_taskflow.py 라우팅

대응 원본: [dags/bakery_book_taskflow.py](../../dags/bakery_book_taskflow.py)

## 역할과 진입점

카페와 베이커리의 서로 다른 업무 날짜를 선택해 병렬 집계하고, 두 보고서를 합쳐 JSON으로 저장하는 TaskFlow DAG다. 마지막의 `bakery_book_taskflow()`가 DAG와 Task 연결을 구성하며, 실제 데이터 처리는 Task 실행 시 수행한다.

| 설정 | 값 |
| --- | --- |
| DAG ID | `bakery_book_taskflow` |
| schedule / catchup / max_active_runs | `None` / `False` / `1` |
| start_date | `2026-01-01`, `Asia/Seoul` |
| tags | `cafe`, `bakery`, `book`, `day05` |
| Param `cafe_date` | 기본 `2026-10-01`, 허용값 `2026-10-01`, `2026-10-02` |
| Param `bakery_date` | 기본 `2026-10-05`, 허용값 `2026-10-05`, `2026-10-06` |

## bakery_book_taskflow()

내부 Task 함수를 정의하고 `read`·`clean`·`summary`를 매장별로 두 번 호출한다. `.override(task_id=...)`로 매장별 Task ID를 지정하며, 반환값 참조가 실행 의존성과 XCom 데이터 전달을 함께 구성한다.

## read(source_path)

`orders.read_orders(source_path)`로 CSV 전체 행을 반환한다. `read_cafe`는 `data/cafe_orders.csv`, `read_bakery`는 `data/bakery_orders.csv`를 읽는다.

## clean(rows, date_key)

컨텍스트의 `params[date_key]`에서 날짜를 읽고 `paid_orders(filter_date(rows, date))`를 반환한다. Task ID는 `clean_cafe`, `clean_bakery`이며 날짜 키는 각각 `cafe_date`, `bakery_date`다. 중복 ID 검사는 하지 않는다.

## summary(rows, date_key)

`orders.summarize(rows)`로 결제 주문을 집계한 뒤 컨텍스트의 선택 날짜를 `report_date`로 추가한다. 집계를 출력하고 사전을 반환한다. Task ID는 `summary_cafe`, `summary_bakery`다. 매출 기준 Variable이나 `target_met` 항목은 사용하지 않는다.

## join(cafe, bakery)

`book_reporting.join_shop_reports(cafe, bakery)`를 반환한다. 두 매장의 날짜를 담은 `report_dates`, 매장별 원본 집계인 `shops`, 두 매출의 합인 `total_revenue`를 만든다. 날짜를 하나로 통일하지 않는다.

## save(report)

합친 보고서를 출력하고 `save_json(report, run_path(get_current_context()["run_id"], "combined.json"))`을 반환한다. 최종 반환값은 저장 경로 문자열이다.

```text
data/cafe_orders.csv   → read_cafe   → clean_cafe   → summary_cafe   ┐
                                                                 ├→ join → save
data/bakery_orders.csv → read_bakery → clean_bakery → summary_bakery ┘
  → outputs/practice/book/day05/<URL 인코딩한 run_id>/combined.json
```

## 결과·실패와 수정 지점

기본 날짜에서는 카페가 결제 3건·수량 4·매출 13000, 베이커리가 결제 3건·수량 6·매출 14000으로 총매출은 27000이다. 상대 경로는 Compose의 `/opt/airflow/workshop`을 기준으로 한다. 같은 실행 ID로 다시 실행하면 같은 JSON을 덮어쓴다.

파일·필수 열·수치 변환 오류와 저장 오류는 해당 Task에 전달되며 별도 예외 처리나 재시도 설정은 없다. 매장 추가는 읽기·정제·집계 분기와 `join_shop_reports` 구조를 함께 변경해야 한다. 날짜 목록은 `Param`, 날짜 선택은 [reports.filter_date](../reports.py.md), 계산·저장은 [orders.py](../orders.py.md), 합치기·출력 경로는 [book_reporting.py](../book_reporting.py.md)에서 변경한다.
