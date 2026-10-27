"""현재 활성 모델을 매번 다시 읽어 판매량을 예측한다."""
import argparse
import json

from bakery_ml import predict_active


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--active", default="outputs/book/day06/ml/registry/active.json")
    parser.add_argument("--expected-visitors", type=float, default=90)
    options = parser.parse_args()
    prediction = predict_active(options.active, options.expected_visitors)
    print(json.dumps(prediction, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()