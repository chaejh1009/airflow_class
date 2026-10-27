# dags/book_dynamic_reports.py 라우팅

대응 원본: [dags/book_dynamic_reports.py](../../dags/book_dynamic_reports.py)

## 역할과 진입점

`STORES` 설정을 순회해 매장별 DAG 2개를 생성한다. 동적 Task 매핑이 아니라 파일 로딩 시 별도 DAG 객체를 등록하는 방식이다.

| DAG ID | 입력 | 목표 매출 | 기본 업무 날짜 |
| --- | --- | ---: | --- |
| `cafe_book_daily` | `data/cafe_orders.csv` | 15000 | `2026-10-01` |
| `bakery_book_daily` | `data/bakery_orders.csv` | 10000 | `2026-10-05` |

두 DAG는 `schedule=None`, `catchup=False`, 시작 `2026-01-01 Asia/Seoul`이며 `max_active_runs`는 명시하지 않는다. `report_date` Param은 문자열이며 enum 제한은 없다.

### `run_store(store, input_path, min_revenue, **context)`

`context["dag_run"].conf.get("report_date", context["params"]["report_date"])`로 실행 설정의 날짜를 우선한다. `make_daily_report(report_date, input_path, min_revenue)`를 호출하고 보고서를 출력한 뒤 `orders.save_json`으로 `outputs/book/day06/dynamic/<store>/<report_date>.json`에 저장한다. 반환값은 파일 경로다.

### `create_store_dag(spec)`

`dag_name(spec["store"])`를 ID로 DAG를 구성하고 `report` PythonOperator를 만든다. `op_kwargs`로 매장명·입력 경로·목표 매출을 `run_store`에 전달한 후 DAG 객체를 반환한다.

```text
STORES → for spec → globals()[dag_name(store)] = create_store_dag(spec)
  → 각 DAG의 report → run_store → make_daily_report → save_json
```

## 결과와 수정 지점

기본 카페 보고서는 매출 `13000`, 목표 `15000`에 미달하며 베이커리는 매출 `14000`, 목표 `10000`을 달성한다. 목표 미달이어도 저장한다. 같은 매장·날짜 파일은 덮어쓴다. 매장 추가·기본값은 `STORES`, DAG 생성은 `create_store_dag`, 날짜 우선순위·저장은 `run_store`, ID 형식은 [book_operations.dag_name](../book_operations.py.md)에서 변경한다.
