import pendulum
from pathlib import Path
from airflow.sdk import DAG, Param, Variable
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from book_reporting import make_report, run_path
from orders import save_json


def report_from_snapshot(report_date, source_path, output_path):
    threshold = int(Variable.get("bakery_min_revenue", default="10000"))
    # [6-H1 · 한 줄] 전달된 복사본 경로로 보고서를 만든다.
    # 예시: result = calculate(day, copied_path, limit)
    report = make_report(report_date, source_path, threshold)
    print(report)
    # [6-H2 · 한 줄] 보고서를 요청 경로에 저장하고 그 경로를 반환한다.
    # 예시: return save_json(result, target)
    return save_json(report, output_path)


with DAG(
    dag_id="bakery_book_files", schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"), catchup=False,
    max_active_runs=1, tags=["bakery", "book", "day05"],
    user_defined_macros={"run_path": run_path},
    params={"report_date": Param("2026-10-05", type="string",
                                enum=["2026-10-05", "2026-10-06", "2026-10-07"])},
):
    snapshot = BashOperator(
        task_id="snapshot",
        # [6-H3 · 한 줄] 폴더 준비 뒤 원본을 복사한다. Bash 명령은 두 줄이다.
        # 예시: bash_command='mkdir -p "$DIR"\ncp "$INPUT" "$OUTPUT"',
        bash_command = 'mkdir -p "$(dirname "$SNAPSHOT_PATH")"\ncp "$SOURCE_PATH" "$SNAPSHOT_PATH"',
        env={"SOURCE_PATH": "data/bakery_orders.csv",
             "SNAPSHOT_PATH": "{{ run_path(run_id, 'orders.csv') }}"},
        append_env=True, cwd=str(Path(__file__).resolve().parent.parent),
    )
    report = PythonOperator(
        task_id="make_report", python_callable=report_from_snapshot,
        op_kwargs={"report_date": "{{ params.report_date }}",
                   "source_path": "{{ run_path(run_id, 'orders.csv') }}",
                   "output_path": "{{ run_path(run_id, 'report.json') }}"},
    )
    # [6-H4 · 한 줄] 복사 성공 뒤 보고서 Task가 실행되게 연결한다.
    # 예시: fetch >> calculate
    snapshot >> report