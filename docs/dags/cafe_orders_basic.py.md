# dags/cafe_orders_basic.py 라우팅

대응 원본: [dags/cafe_orders_basic.py](../../dags/cafe_orders_basic.py)

## 역할과 진입점

카페 CSV를 읽고 결제 주문의 건수·수량·매출을 JSON으로 저장하는 DAG다. `pendulum`, `airflow.sdk`의 `dag`·`task`, [orders.py](../orders.py.md)의 공통 함수 4개를 사용한다.

파일 마지막의 `cafe_orders_basic()` 호출이 DAG와 Task 관계를 구성한다. 이때 중첩된 Task 호출은 실행 의존성을 구성하며, 실제 CSV 읽기와 저장은 Airflow가 Task를 실행할 때 수행한다.

## DAG 설정

| 설정 | 값·의미 |
| --- | --- |
| DAG ID | `cafe_orders_basic` |
| schedule | `None`: 정기 실행 스케줄 없음 |
| start_date | `2026-01-01`, `Asia/Seoul` |
| catchup | `False` |
| max_active_runs | `1`: 동시 활성 DAG Run 수 제한 |
| tags | `cafe`, `beginner` |

## 함수·Task별 경로

| 함수 서명 | 호출·입력 | 하위 호출 | 결과 |
| --- | --- | --- | --- |
| `cafe_orders_basic()` | 파일 최하단에서 호출 | 내부 Task 정의 및 `save(total(keep_paid(read())))` | DAG 구성 |
| `read()` | 시작 Task, 인자 없음 | `orders.read_orders()` | `data/cafe_orders.csv`의 행 리스트 |
| `keep_paid(rows)` | `read` 반환값 | `orders.paid_orders(rows)` | 결제 행 리스트 |
| `total(rows)` | `keep_paid` 반환값 | `orders.summarize(rows)` | 집계 사전 |
| `save(summary)` | `total` 반환값 | `orders.save_json(summary, "outputs/day04-summary.json")` → `print(summary)` | 저장 경로 문자열 |

내부 Task 함수는 모두 `cafe_orders_basic` 안에 정의된다. Task ID는 각각 `read`, `keep_paid`, `total`, `save`다.

```text
data/cafe_orders.csv
  → read → keep_paid → total → save → outputs/day04-summary.json
                                └─→ summary를 Task 로그에 출력
```

TaskFlow 반환값 참조로 의존성을 연결하고, 실행 시 Task 결과를 XCom으로 전달한다. `save`의 최종 반환값은 집계 사전이 아니라 `outputs/day04-summary.json`이라는 경로 문자열이다.

## 입출력과 실패 경로

현재 데이터는 전체 8행 중 결제 6행이며, 저장 결과는 `{"order_count": 6, "quantity": 10, "revenue": 32500}`이다. 모든 날짜를 합산하며, 파일명의 `day04`가 날짜 필터를 의미하지는 않는다.

상대 경로는 작업 디렉터리를 기준으로 해석된다. Compose 사용 시 출력은 호스트의 `outputs/day04-summary.json`에도 반영된다. 재실행하면 같은 파일을 덮어쓴다.

파일 읽기 오류는 `read`, 상태 키 오류는 `keep_paid`, 수량·단가 오류는 `total`, 저장 권한·직렬화 오류는 `save`에서 발생한다. 코드에 별도 예외 처리나 Task별 재시도 설정은 없다.

## 수정 지점

입력 경로는 `read`의 `read_orders` 인자, 출력 경로는 `save`의 `save_json` 인자, 실행 순서는 마지막 Task 연결식에서 변경한다. 스케줄은 `@dag` 설정에서, 공통 계산은 `orders.py`에서 변경한다.
