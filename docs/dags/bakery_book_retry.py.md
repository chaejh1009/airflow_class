# dags/bakery_book_retry.py 라우팅

대응 원본: [dags/bakery_book_retry.py](../../dags/bakery_book_retry.py)

## 역할과 진입점

일시 오류와 지속 오류를 비교하는 단일 Task DAG다. 모듈의 `with DAG(...)`가 `bakery_book_retry`를 구성한다. `schedule=None`, `catchup=False`, 시작은 `2026-01-01 Asia/Seoul`이며 `max_active_runs`는 명시하지 않는다.

| Param | 기본값 | 의미 |
| --- | --- | --- |
| `report_date` | `2026-10-05` | 문자열 업무 날짜, enum 제한 없음 |
| `simulate_failure` | `false` | 첫 시도에만 오류 발생 |
| `always_fail` | `false` | 모든 시도에 오류 발생 |

### `read_day(**context)`

params와 `context["ti"].try_number`를 [book_operations.attempt_report](../book_operations.py.md)에 전달한다. 성공하면 보고서를 출력하고 반환한다.

```text
read_report (PythonOperator, read_day)
  → attempt_report → make_daily_report → orders.read_orders → reports.build_report
  → 로그·반환값 XCom
```

## 결과와 수정 지점

`retries=1`, `retry_delay=5초`이므로 최초 실행을 포함해 최대 2번 시도한다. 일시 실패를 켜면 첫 시도 실패 후 재시도에서 성공하고, 지속 실패를 켜면 최종 실패한다. 기본 날짜의 매출은 `14000`이며 파일 저장은 없다. 오류 조건은 `attempt_report`, 횟수·간격은 Operator, 입력은 DAG params에서 변경한다.
