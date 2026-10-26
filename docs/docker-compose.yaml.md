# docker-compose.yaml 라우팅

대응 원본: [docker-compose.yaml](../docker-compose.yaml)

## 역할과 시작 경로

Airflow 서비스 한 개와 상태 저장 볼륨을 정의하는 실행 설정이다. Python 함수는 없으며, Docker Compose가 `services.airflow`를 읽어 컨테이너를 구성한다.

```text
Docker Compose
  → services.airflow
  → apache/airflow:3.1.8-python3.12
  → standalone 명령
  → /opt/airflow/workshop/dags의 DAG 로딩
  → DAG의 공통 모듈 import → orders.py / reports.py / workflow_day05.py / book_reporting.py
```

## 설정별 연결

| 설정 | 값 | 연결 의미 |
| --- | --- | --- |
| `image` | `apache/airflow:3.1.8-python3.12` | Airflow 실행 이미지 |
| `command` | `standalone` | 컨테이너 시작 명령 |
| `working_dir` | `/opt/airflow/workshop` | 코드의 상대 경로 기준 |
| `ports` | `127.0.0.1:8080:8080` | 호스트 로컬 주소 8080 → 컨테이너 8080 |
| `AIRFLOW_HOME` | `/opt/airflow` | Airflow 홈 경로 |
| `AIRFLOW__CORE__DAGS_FOLDER` | `/opt/airflow/workshop/dags` | DAG 검색 경로 |
| `AIRFLOW__CORE__LOAD_EXAMPLES` | `"false"` | 기본 예제 DAG 로딩 비활성화 |
| `PYTHONPATH` | `/opt/airflow/workshop` | DAG에서 루트의 공통 Python 모듈을 import할 경로 |
| `MODEL_OPS_ROOT` | `/opt/airflow/workshop/artifacts` | 환경 변수만 정의됨. 현재 Python 코드에서는 참조하지 않음 |

## 호스트·컨테이너 경로 대응

| 볼륨 또는 호스트 경로 | 컨테이너 경로 | 사용처 |
| --- | --- | --- |
| 명명 볼륨 `airflow-state` | `/opt/airflow` | Airflow 상태 보존 |
| 프로젝트 루트 `.` | `/opt/airflow/workshop` | 프로젝트 전체 바인드 마운트 |
| `./dags/` | `/opt/airflow/workshop/dags/` | DAG 파일 |
| `./orders.py` | `/opt/airflow/workshop/orders.py` | 공통 함수 모듈 |
| `./reports.py`, `./workflow_day05.py`, `./book_reporting.py` | `/opt/airflow/workshop/` 아래 같은 파일명 | 날짜 선택·보고서·실행별 저장 모듈 |
| `./data/` | `/opt/airflow/workshop/data/` | CSV 읽기 |
| `./outputs/` | `/opt/airflow/workshop/outputs/` | 카페 JSON, day05 실행별 CSV 복사본·보고서·결합 JSON 저장 |

표의 개별 파일·폴더 경로는 별도 볼륨 선언이 아니라 프로젝트 루트 마운트에 포함된다. `airflow-state`는 별도 명명 볼륨이다. 호스트 `config/`를 Airflow 설정 경로로 연결하는 별도 설정은 없다. 파일 및 XCom 보고서 실습은 Task들이 같은 `outputs/` 파일에 접근할 수 있는 이 구성을 사용한다.

## 수정 지점과 확인 사항

접속 포트는 `ports`, 실행 이미지 버전은 `image`, DAG 위치는 `AIRFLOW__CORE__DAGS_FOLDER`에서 변경한다. 프로젝트 마운트 위치를 바꾸면 `working_dir`, `PYTHONPATH`, DAG 경로도 함께 확인해야 한다. 이 설정이 맞지 않으면 모듈 import 또는 상대 경로 CSV 읽기가 실패할 수 있다.

이 파일에는 별도 빌드 설정, 추가 패키지 설치 단계, 외부 데이터베이스 서비스가 없다. DAG의 업무 흐름과 저장 목적지는 각각의 Python 파일에서 정의한다.
