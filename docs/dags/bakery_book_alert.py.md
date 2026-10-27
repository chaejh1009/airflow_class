# dags/bakery_book_alert.py 라우팅

대응 원본: [dags/bakery_book_alert.py](../../dags/bakery_book_alert.py)

## 역할과 진입점

최종 실패 시 콜백을 실행하는 단일 Task DAG다. 모듈의 `with DAG(...)`가 `bakery_book_alert`를 구성한다. `schedule=None`, `catchup=False`, 시작은 `2026-01-01 Asia/Seoul`이며 `max_active_runs`는 명시하지 않는다. 문자열 Param `report_date`는 `2026-10-05`, boolean Param `always_fail`은 `false`가 기본이다.

### `read_day(**context)`

`attempt_report(params["report_date"], False, context["ti"].try_number, params["always_fail"])`를 반환한다. 일시 실패는 끄고 지속 실패만 입력으로 제어한다.

```text
read_report (PythonOperator, read_day, retries=1, retry_delay=5초)
  → attempt_report → 보고서 반환
  → 재시도 소진 후 실패 → discord_failure_notice(context)
                         → failure_notice → 로그 → 웹훅 전송 경로
```

## 콜백과 수정 지점

현재 `on_failure_callback=discord_failure_notice`이며 함께 import한 `failure_notice`가 직접 연결된 것은 아니다. [book_operations.py](../book_operations.py.md)의 웹훅 URL이 빈 문자열이므로 최종 실패 시 payload 로그를 남긴 뒤 콜백도 `ValueError`로 실패한다. 현재 설정에서는 Discord에 전송되지 않는다. 로그만 확인하려면 콜백을 `failure_notice`로 연결할 수 있다. 성공 시 매출 보고서를 반환하며 파일 저장은 없다. 콜백 선택·재시도는 Operator, payload·전송은 공통 모듈에서 변경한다.
