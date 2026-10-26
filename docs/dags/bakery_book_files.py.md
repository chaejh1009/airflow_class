# dags/bakery_book_files.py 라우팅

대응 원본: [dags/bakery_book_files.py](../../dags/bakery_book_files.py)

## 역할과 진입점

원본 CSV를 실행별 폴더에 복사한 다음 그 복사본으로 보고서를 만드는 DAG다. 모듈의 `with DAG(...)`가 두 Operator와 실행 의존성을 등록한다. Task 사이에는 같은 파일 경로를 템플릿으로 지정하며 XCom 반환값을 인자로 연결하지 않는다.

| 설정 | 값 |
| --- | --- |
| DAG ID | `bakery_book_files` |
| schedule / catchup / max_active_runs | `None` / `False` / `1` |
| start_date | `2026-01-01`, `Asia/Seoul` |
| tags | `bakery`, `book`, `day05` |
| Param `report_date` | 기본 `2026-10-05`, 허용값 `2026-10-05`, `2026-10-06`, `2026-10-07` |
| 사용자 매크로 | `run_path`: 실행 ID를 URL 인코딩한 출력 경로 생성 |

## snapshot Task

`BashOperator`는 프로젝트 루트를 `cwd`로 사용한다. 환경 변수 `SOURCE_PATH`는 `data/bakery_orders.csv`, `SNAPSHOT_PATH`는 `{{ run_path(run_id, 'orders.csv') }}`다. `append_env=True`로 기존 환경도 유지한다.

```text
snapshot
  → mkdir -p "$(dirname "$SNAPSHOT_PATH")"
  → cp "$SOURCE_PATH" "$SNAPSHOT_PATH"
  → outputs/practice/book/day05/<인코딩한 run_id>/orders.csv
```

두 명령은 줄바꿈으로 구분되어 있고 `&&`나 `set -e`는 없다. 입력 파일이 없거나 복사 권한이 없으면 `cp` 실패로 Task가 실패한다. 스냅샷에는 선택 날짜만이 아니라 원본 전체 행이 포함된다.

## report_from_snapshot(report_date, source_path, output_path)

`make_report` PythonOperator의 호출 대상이다. 날짜와 입출력 경로는 `op_kwargs`에서 템플릿으로 렌더링한다.

```text
snapshot 성공 → make_report
  → int(Variable.get("bakery_min_revenue", default="10000"))
  → book_reporting.make_report(report_date, source_path, threshold)
      → 복사한 orders.csv 읽기 → 날짜·paid 선택 → 집계·목표 비교
  → 보고서 로그 출력
  → orders.save_json(report, output_path)
  → outputs/practice/book/day05/<인코딩한 run_id>/report.json 경로 반환
```

기본 날짜와 기준에서는 결제 3건, 수량 6, 매출 14000, 목표 달성이다. 반환값은 보고서 사전이 아니라 저장 경로 문자열이며 자동 XCom에 기록된다. `snapshot >> report`가 순서를 보장한다.

## 경로·실패와 수정 지점

경로 형식은 [book_reporting.run_path](../book_reporting.py.md)가 결정한다. 같은 실행 ID로 재실행하면 같은 파일을 덮어쓴다. 이 경로에는 DAG ID가 없으므로 다른 보고서 DAG와 실행 ID가 같으면 `report.json` 경로도 겹친다. 두 Task가 같은 파일을 볼 수 있는 파일시스템이 필요하며, 현재 Compose는 프로젝트 전체를 하나의 컨테이너에 마운트한다.

`snapshot`의 입력·작업 경로와 `make_report`의 템플릿 경로는 함께 맞춘다. Python의 상대 경로는 현재 작업 디렉터리를 기준으로 하므로 Compose의 `working_dir` 설정도 확인한다. 정수 변환·파일·CSV·직렬화 오류는 별도 처리 없이 Task에 전달된다.
