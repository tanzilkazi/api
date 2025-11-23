# src/exercises/day01_request_basics.py

"""
Day 01–02: Requests, retries, sessions

Goal:
- Get comfortable with basic GET calls
- Compare one-off requests vs a shared session
- Inspect status codes, headers, and simple error handling
"""

import logging
import requests
import time
from src.config import setup_logging, make_session

LOGGER = logging.getLogger(__name__)
TEST_URL = "https://httpbin.org/get"


def e01_simple_get() -> None:
    print("\n=== simple_get ===")
    try:
        resp = requests.get(TEST_URL, timeout=10)
    except Exception as e:
        print(f"simple_get: EXCEPTION: {e!r}")
        return

    print(f"simple_get: status={resp.status_code}")
    print(f"simple_get: first 120 chars:\n{resp.text[:120]!r}")
    LOGGER.info("simple_get: status=%s", resp.status_code)

def e00_session_get() -> None:
    print("\n=== session_get ===")
    session = make_session()
    try:
        resp = session.get(TEST_URL, timeout=10)
    except Exception as e:
        print(f"session_get: EXCEPTION: {e!r}")
        return

    print(f"session_get: status={resp.status_code}")
    print(f"session_get: first 120 chars:\n{resp.text[:120]!r}")
    LOGGER.info("session_get: status=%s", resp.status_code)

def e01_compare_requests_sessions() -> None:
    print("\n=== compare_requests_sessions ===")

    repeats = 10

    request_time = 0.0
    for i in range(repeats):
        # new request created each time
        resp1 = requests.get(TEST_URL, timeout=10)
        request_time += resp1.elapsed.total_seconds()
    print(f"compare_requests_sessions: requests.get avg time: {request_time / repeats:.4f}s")

    # single instance of session that's reused
    session = make_session()
    session_time = 0.0
    for i in range(repeats):
        resp2 = session.get(TEST_URL, timeout=10)
        session_time += resp2.elapsed.total_seconds()
    print(f"compare_requests_sessions: session.get avg time: {session_time / repeats:.4f}s")
    
def e02_force_timeout() -> None:
    # force a timeout by setting a very low timeout value and catch it
    try:
        resp = requests.get(TEST_URL, timeout=1)
    except requests.RequestException as e:
        print(f"force_timeout: Caught timeout as expected: {e!r}")
        return
    
def e04_inspect_headers() -> None:
    print("\n=== inspect_headers ===")
    resp = requests.get(TEST_URL, timeout=10)
    print("Response Headers:")

    for key, value in resp.headers.items():
        print(f"  {key}: {value}")

def e05_retry_logic() -> None:
    print("\n=== retry_logic ===")
    session = make_session()
    for attempt in range(3):
        print(f"retry_logic: Attempt {attempt + 1}/3")
        try:
            resp = session.get(TEST_URL, timeout=10)
        except requests.exceptions.Timeout as e:
            print(f"retry_logic: Timeout: {e!r} -> retrying...")
        except requests.exceptions.ConnectionError as e:
            print(f"retry_logic: Connection Error: {e!r} -> retrying...")
        except Exception as e:
            print(f"retry_logic: Non-retryable: {e!r}")
            return
        else:   
            if 500 <= resp.status_code < 600:
                print(f"retry_logic: Server error {resp.status_code}, retrying...")
            elif resp.status_code > 400:
                print(f"retry_logic: Client error {resp.status_code}, not retrying.")
                break
            else: 
                print(f"retry_logic: Success {resp.status_code}")
                break
            time.sleep(0.5)  # simple backoff


    print(f"retry_logic: status={resp.status_code}")
    LOGGER.info("retry_logic: status=%s", resp.status_code)

def main() -> None:
    setup_logging(logging.DEBUG)
    print("Running Day 01 requests demo...")
    #e00_simple_get()
    #e00_session_get()
    #e01_compare_requests_sessions()
    e05_retry_logic()
    
    print("\nDone Day 01.")

if __name__ == "__main__":
    main()
