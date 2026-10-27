# dags/bakery_book_ml.py 라우팅

대응 원본: [dags/bakery_book_ml.py](../../dags/bakery_book_ml.py)

## 역할과 진입점

수요 데이터 변경을 확인하고 회귀 모델을 학습·평가·승인한 뒤 예측하는 DAG다. 모듈의 `with DAG(...)`가 `bakery_book_ml`을 구성한다. `schedule="*/1 * * * *"`로 매분 실행하며 `catchup=False`, `max_active_runs=1`, 시작은 `2026-01-01 Asia/Seoul`이다.

| Param | 기본값 | 검증 |
| --- | --- | --- |
| `source_path` | `data/bakery_demand.csv` | 문자열 |
| `max_mae` | `3.0` | 0 이상의 숫자 |
| `expected_visitors` | `90` | 0 이상의 숫자 |

### `prepare_task(**context)`

`bakery_ml.prepare_data(params["source_path"], run_id)`를 호출한다. 반환값이 `None`이면 `AirflowSkipException`으로 데이터 미변경 실행을 건너뛰고, 아니면 준비 JSON 경로를 반환한다. Task ID는 `prepare`다.

### `train_task(**context)`

`prepare` XCom 경로를 `train_model`에 전달하고 후보 모델 경로를 반환한다. Task ID는 `train`이다.

### `evaluate_task(**context)`

`train` XCom 경로와 `params["max_mae"]`를 `evaluate_model`에 전달하고 평가 JSON 경로를 반환한다. Task ID는 `evaluate`다.

### `approve_task(**context)`

`evaluate` XCom 경로를 `approve_model`에 전달한다. 품질 미달로 `None`이면 `AirflowSkipException`을 발생시키고, 승인되면 활성 JSON 경로를 반환한다. Task ID는 `approve`다.

### `predict_task(**context)`

`approve`의 활성 경로, `evaluate`의 평가 경로와 방문객 Param을 읽는다. `predict_active` 결과를 평가 JSON과 같은 폴더의 `prediction.json`에 `bakery_ml.save_json`으로 저장한다. Task ID는 `predict`이며 반환값은 저장 경로다.

```text
prepare → train → evaluate → approve → predict
   준비 JSON → 후보 joblib → 평가 JSON → 활성 JSON → 예측 JSON
```

## 결과·건너뛰기와 수정 지점

Task 간 XCom에는 모델 객체 대신 파일 경로를 전달한다. 파일은 `outputs/book/day06/ml/` 아래 실행 폴더와 공용 레지스트리에 저장한다. 마지막 승인·거절 데이터와 동일하면 `prepare`부터, 품질 미달이면 `approve`부터 후속 Task가 skipped된다. 거절 시 기존 활성 모델은 보존하며 이 실행의 예측 Task는 실행하지 않는다. 별도 재시도 설정은 없다.

주기·기본값·연결은 이 DAG, 분할·학습·승인·파일 재사용은 [bakery_ml.py](../bakery_ml.py.md), 활성 모델만 이용한 독립 예측은 [predict_bakery_demand.py](../predict_bakery_demand.py.md)에서 확인한다. `joblib`·`scikit-learn`을 DAG를 파싱하고 실행하는 환경에 설치해야 한다. 현재 Compose에는 추가 패키지 설치 단계가 없다.
