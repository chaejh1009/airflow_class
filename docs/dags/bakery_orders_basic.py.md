# dags/bakery_orders_basic.py 라우팅

대응 원본: [dags/bakery_orders_basic.py](../../dags/bakery_orders_basic.py)

## 역할과 진입점

베이커리 CSV의 결제 주문을 집계하는 DAG다. `pendulum`, `airflow.sdk`의 `dag`·`task`, [orders.py](../orders.py.md)의 `read_orders`, `paid_orders`, `summarize`를 사용한다. `bakery_practice.py`는 import하거나 호출하지 않는다.

파일 마지막의 `bakery_orders_basic()`이 DAG를 구성한다. 내부 Task 연결식은 실행 관계를 정의하며, 데이터 처리는 Airflow가 Task를 실행할 때 수행한다.

## DAG 설정

| 설정 | 값·의미 |
| --- | --- |
| DAG ID | `bakery_orders_basic` |
| schedule | `None`: 정기 실행 스케줄 없음 |
| start_date | `2026-01-01`, `Asia/Seoul` |
| catchup | `False` |
| max_active_runs | `1`: 동시 활성 DAG Run 수 제한 |
| tags | `bakery`, `beginner` |

## 함수·Task별 경로

| 함수 서명 | 호출·입력 | 하위 호출 | 결과 |
| --- | --- | --- | --- |
| `bakery_orders_basic()` | 파일 최하단에서 호출 | 내부 Task 정의 및 `total(keep_paid(read()))` | DAG 구성 |
| `read()` | 시작 Task, 인자 없음 | `orders.read_orders("data/bakery_orders.csv")` | 베이커리 행 리스트 |
| `keep_paid(rows)` | `read` 반환값 | `orders.paid_orders(rows)` | 결제 행 리스트 |
| `total(rows)` | `keep_paid` 반환값 | `orders.summarize(rows)` | 집계 사전 |

내부 Task 함수는 모두 `bakery_orders_basic` 안에 정의된다. Task ID는 각각 `read`, `keep_paid`, `total`이다.

```text
data/bakery_orders.csv → read → keep_paid → total → 집계 반환값 (XCom)
```

TaskFlow 반환값 참조로 실행 의존성을 연결하고 Task 결과를 전달한다. 현재 데이터는 전체 8행 중 결제 6행이며, 최종 집계는 `{"order_count": 6, "quantity": 10, "revenue": 22500}`이다. 날짜별 그룹화는 없다.

## 출력과 실패 경로

저장 Task와 `save_json` 호출이 없으므로 JSON 파일을 생성하지 않는다. 기존 `outputs/practice/day04-summary.json`을 이 DAG의 출력으로 간주하면 안 된다.

입력 경로는 현재 작업 디렉터리를 기준으로 한다. 파일 오류는 `read`, 상태 키 오류는 `keep_paid`, 수량·단가의 누락 또는 정수 변환 오류는 `total`에서 발생한다. 코드에 별도 예외 처리나 Task별 재시도 설정은 없다.

## 수정 지점

입력 파일은 `read`, Task 순서는 마지막 연결식, 실행 설정은 `@dag`에서 변경한다. 결제 선택과 집계 방식은 `orders.py`에서 변경하며, 카페 DAG에도 영향을 준다. 베이커리 실습 모듈을 수정하는 것만으로는 이 DAG의 동작이 바뀌지 않는다.
