# dags/bakery_book_operator.py 라우팅

대응 원본: [dags/bakery_book_operator.py](../../dags/bakery_book_operator.py)

## 역할과 진입점

`PythonOperator` 하나에서 업무 날짜별 베이커리 보고서를 만드는 DAG다. 모듈의 `with DAG(...)` 블록이 DAG와 Task를 등록하며, 보고서 계산과 Variable 조회는 Task 실행 시 이루어진다.

| 설정 | 값 |
| --- | --- |
| DAG ID / Task ID | `bakery_book_operator` / `make_report` |
| schedule / catchup / max_active_runs | `None` / `False` / `1` |
| start_date | `2026-01-01`, `Asia/Seoul` |
| tags | `bakery`, `book`, `day05` |
| Param `report_date` | 기본 `2026-10-05`, 허용값 `2026-10-05`, `2026-10-06`, `2026-10-07` |

## report_for_date(report_date)

`make_report` Task의 `python_callable`이다. `op_kwargs`의 `{{ params.report_date }}`가 실행 시 업무 날짜 문자열로 렌더링된다.

```text
params.report_date → make_report Task → report_for_date(report_date)
  → int(Variable.get("bakery_min_revenue", default="10000"))
  → book_reporting.make_report(report_date, min_revenue=threshold)
      → orders.read_orders("data/bakery_orders.csv")
      → reports.build_report → 날짜 선택 → paid 선택 → 집계 → 목표 비교
  → 보고서 로그 출력 → 보고서 사전 반환 (자동 XCom)
```

업무 날짜는 Airflow 실행 날짜와 별개인 Param이다. 기본 입력·기준에서는 결제 3건, 수량 6, 매출 14000, `target_met=True`다. 결과 키는 `report_date`, `order_count`, `quantity`, `revenue`, `min_revenue`, `target_met`이다. JSON 파일은 저장하지 않는다.

## 예외와 수정 지점

Variable 값이 정수 문자열이 아니면 `int` 변환이 실패한다. 파일·열·수치 오류는 [book_reporting.py](../book_reporting.py.md), [reports.py](../reports.py.md), [orders.py](../orders.py.md)를 거쳐 Task 실패로 전달된다. 별도 예외 처리나 재시도 설정은 없다.

허용 날짜는 `Param`, 기준값의 키·기본값은 `report_for_date`, 전달 방식은 `PythonOperator.op_kwargs`, 업무 계산은 공통 보고서 모듈에서 변경한다.
