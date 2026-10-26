# dags/bakery_book_xcom.py 라우팅

대응 원본: [dags/bakery_book_xcom.py](../../dags/bakery_book_xcom.py)

## 역할과 진입점

JSON 보고서의 경로를 명시적 XCom 키로 보내는 방식과 반환값으로 보내는 방식을 비교한다. 모듈에 있는 두 `with DAG(...)` 블록이 각각 DAG 하나를 등록한다.

| 설정 | 두 DAG의 값 |
| --- | --- |
| DAG ID | `bakery_book_xcom_explicit`, `bakery_book_xcom_return` |
| Task 순서 | `make_report → read_report` |
| schedule / catchup / max_active_runs | `None` / `False` / `1` (DAG별) |
| start_date | `2026-01-01`, `Asia/Seoul` |
| tags | `bakery`, `book`, `day05` |
| Param `report_date` | 기본 `2026-10-05`, 허용값 `2026-10-05`, `2026-10-06`, `2026-10-07` |

두 생산 함수 모두 실행 컨텍스트의 날짜·실행 ID와 정수로 변환한 Variable `bakery_min_revenue`(기본 `10000`)를 사용한다. 파일 저장과 읽기는 [book_reporting.py](../book_reporting.py.md)에 위임한다.

## produce_explicit()

`bakery_book_xcom_explicit.make_report`의 호출 대상이다. `get_current_context()` → `Variable.get` → `write_report(report_date, run_id, threshold)`로 JSON을 저장하고, 반환받은 경로를 `context["ti"].xcom_push(key="report_path", value=path)`로 보낸다. 함수 자체의 반환값은 `None`이다.

## consume_explicit()

`bakery_book_xcom_explicit.read_report`의 호출 대상이다. 같은 DAG Run의 `make_report`에서 `xcom_pull(task_ids="make_report", key="report_path")`로 경로를 받아 `read_report(path)`로 JSON을 읽는다. 날짜와 매출을 출력하고 보고서 사전을 반환한다.

## produce_return()

`bakery_book_xcom_return.make_report`의 호출 대상이다. 컨텍스트와 Variable을 읽는 흐름은 명시적 방식과 같지만 `write_report(...)`의 경로를 바로 반환한다. PythonOperator가 반환값을 기본 XCom 키 `return_value`로 전달한다.

## consume_return()

`bakery_book_xcom_return.read_report`의 호출 대상이다. `xcom_pull(task_ids="make_report")`로 기본 반환 키의 경로를 얻고 JSON을 읽는다. 날짜·매출을 출력한 뒤 보고서 사전을 반환한다.

```text
명시적 DAG: make_report → write_report → report.json
                         └─ xcom_push(report_path) → read_report Task
                                                     → xcom_pull(report_path) → JSON 읽기
반환값 DAG: make_report → write_report → report.json
                         └─ return 경로 → XCom(return_value) → read_report Task
                                                              → xcom_pull() → JSON 읽기
```

## 출력·실패와 수정 지점

저장 위치는 `outputs/practice/book/day05/<URL 인코딩한 run_id>/report.json`이다. XCom으로 넘기는 생산 결과는 파일 경로이며, 소비 Task가 파일을 다시 연다. 기본 날짜에서는 매출 14000, 기준 10000으로 목표 달성이다.

Task들은 같은 파일을 볼 수 있어야 한다. 경로에 DAG ID가 없으므로 두 DAG 또는 `bakery_book_files`에서 같은 실행 ID를 사용하면 저장 위치가 겹칠 수 있다. DAG별 `max_active_runs=1`은 이 충돌을 막지 않는다. 재실행하면 같은 경로를 덮어쓴다.

생산이 실패하면 후속 소비는 실행되지 않는다. 잘못된 Variable 정수, 누락된 XCom 경로, 파일 접근·JSON 파싱 오류는 별도 처리하지 않는다. 명시적 키를 바꿀 때는 push와 pull을 함께 바꾸고, 업무 계산은 공통 보고서 모듈에서 변경한다.
