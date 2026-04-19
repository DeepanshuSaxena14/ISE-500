import requests
from mock_data import (
    MOCK_DRIVERS_PAYLOAD,
    MOCK_VEHICLES_PAYLOAD,
    MOCK_DRIVER_PERFORMANCE_PAYLOAD,
    MOCK_LOAD_REQUESTS,
)

BASE_URL = "http://127.0.0.1:8000"


def show(label, resp):
    print(f"\n=== {label} ===")
    print("status:", resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


def main():
    r = requests.post(f"{BASE_URL}/ingest/drivers", json=MOCK_DRIVERS_PAYLOAD)
    show("ingest drivers", r)

    r = requests.post(f"{BASE_URL}/ingest/vehicles", json=MOCK_VEHICLES_PAYLOAD)
    show("ingest vehicles", r)

    r = requests.post(
        f"{BASE_URL}/ingest/driver-performance",
        json=MOCK_DRIVER_PERFORMANCE_PAYLOAD,
    )
    show("ingest driver performance", r)

    r = requests.get(f"{BASE_URL}/health")
    show("health", r)

    r = requests.get(f"{BASE_URL}/driver-cards")
    show("driver cards", r)

    for load_req in MOCK_LOAD_REQUESTS:
        r = requests.post(f"{BASE_URL}/loads", json=load_req)
        show("create load", r)

        if r.ok:
            load_id = r.json()["id"]

            r = requests.get(f"{BASE_URL}/loads/{load_id}")
            show("get load", r)

            r = requests.get(f"{BASE_URL}/loads/{load_id}/recommendations")
            show("recommendations", r)

            r = requests.get(f"{BASE_URL}/loads/{load_id}/recommendation/top")
            show("top recommendation", r)


if __name__ == "__main__":
    main()