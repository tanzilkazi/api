"""API client wrapper for Guardian requests.

Provides a small `BaseClient` that performs HTTP requests to the
Guardian API and a convenience `get_all_articles` method that pages
through results. Keep secrets out of logs (do not log `api-key`).
"""

import logging
import time
from datetime import timedelta, datetime
import random
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
import requests
import src.api_client.config as config
import src.api_client.errors as errors
import json

class BaseClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 10) -> None:
        """
        - function: BaseClient.__init__
        - logic: Store configuration values and prepare a `requests.Session`.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.session = requests.Session()

    def _backoff_sleep_jitter(self, attempt: int, max_backoff:float, base_backoff:float, retry_after:float | None = None) -> float:
        """
        - function: BaseClient._backoff_sleep_jitter
        - logic: calculates sleep_time and sleeps. Adds jitter and takes into 
                 account retry_after from server).
        """
        if retry_after is not None:
            sleep_time = min(max_backoff, float(retry_after))
        else:
            sleep_time = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
        sleep_time += random.uniform(0, sleep_time * 0.5)
        time.sleep(sleep_time)
        return sleep_time
        
    #TODO: implement generator
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] | None = None,
    ) -> requests.Response:
        """
        - function: BaseClient._request
        - logic: Build URL, attach `api-key` to params, perform an HTTP request
                 with `self.session`, and map common HTTP status codes to
                 domain-specific exceptions. Logs at DEBUG level (avoid logging
                 secrets in production).
        """
        url = f"{self.base_url}{endpoint}"
        #session = requests.Session()
        
        if params is None:
            params = {}

        # Make a local copy so we don't mutate the caller's dict
        request_params = dict(params)
        request_params["api-key"] = self.api_key

        # Create a redacted copy for logging so secrets aren't written to logs
        safe_params = dict(request_params)
        for secret_key in ("api-key", "api_key", "key", "access_token", "token"):
            if secret_key in safe_params:
                safe_params[secret_key] = "<REDACTED>"

        # Use %-style args to defer formatting when DEBUG is disabled
        self.logger.debug("Making %s request to %s with params %s", method, url, safe_params)

        # Retry/backoff configuration
        max_retries = 4
        base_backoff = 1.0  # seconds
        max_backoff = 30.0  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.request(method, url, params=request_params, timeout=self.timeout)
            except requests.Timeout as e:
                # treat timeout as transient
                if attempt == max_retries:
                    raise errors.APITimeoutError(f"Request timeout error {e}") from e
                
                # sleep_time = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
                # sleep_time += random.uniform(0, sleep_time * 0.5)
                sleep_time = self._backoff_sleep_jitter(attempt, max_backoff, base_backoff)
                self.logger.debug("Timeout on attempt %d, sleeping %.2fs then retrying", attempt, sleep_time)
                # time.sleep(sleep_time)
                continue
            except requests.RequestException as e:
                # network-level errors (DNS, connection reset, etc.) — retry
                if attempt == max_retries:
                    raise errors.APIConnectionError(f"Network error while calling {url}: {e}") from e
                sleep_time = self._backoff_sleep_jitter(attempt, max_backoff, base_backoff)
                self.logger.debug("RequestException on attempt %d, sleeping %.2fs then retrying", attempt, sleep_time)
                time.sleep(sleep_time)
                continue

            status = resp.status_code

            # Successful response
            if status == 200:
                return resp

            # Authentication errors — don't retry
            if status in (401, 403):
                raise errors.APIAuthError(f"Authentication error: {status}")

            # Client errors (other than 429) are not retried
            if 400 <= status < 500 and status != 429:
                raise errors.APIClientError(f"Client error: {status}")

            # Rate limiting (429) or server errors (5xx) — may retry
            if status == 429 or 500 <= status < 600:
                # If server supplied Retry-After, honor it (if it's an integer)
                retry_after = None
                ra = resp.headers.get("Retry-After")
                if ra:
                    try:
                        retry_after = int(ra)
                    except ValueError:
                        retry_after = None

                if attempt == max_retries:
                    if status == 429:
                        raise errors.APIClientError(f"Rate limit exceeded: {status}")
                    else:
                        raise errors.APIServerError(f"Server error: {status}")

                # add jitter
                sleep_time = self._backoff_sleep_jitter(attempt, max_backoff, base_backoff, retry_after)
                self.logger.debug("Received status %d on attempt %d, sleeping %.2fs then retrying", status, attempt, sleep_time)
                time.sleep(sleep_time)
                continue

    def get_all_articles(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        - function: BaseClient.get_all_articles
        - inputs: params: Dict[str, Any] (query parameters for the API)
        - outputs: List of raw result dicts from the Guardian API
        - logic: Paginate through search results by setting `page` in `params`,
                 calling `_request` for each page and aggregating `response.results`.
                 Returns the combined list when all pages are fetched.
        """
        page = 1
        results = None
        while True:
            params['page'] = page
            try:
                response = self._request("GET", "/search", params)
            except Exception as e:
                raise e
            data = response.json()
            if results is None:
                results = data.get('response', {}).get('results', [])
            else:
                results.extend(data.get('response', {}).get('results', []))
            if data.get('response', {}).get('currentPage', 0) >= data.get('response', {}).get('pages', 0):
                print(f"Fetched total {len(results)} articles.")
                break
            page += 1
        return results
        


def main() -> None:
    """
    - function: main
    - inputs: none (reads env vars)
    - outputs: prints counts, returns None
    - logic: Quick manual runner for `BaseClient` that fetches yesterday's
             articles and prints the number of results. Intended for local
             smoke testing.
    """
    load_dotenv()
    # TODO: change to get_env utility function
    api_key = os.getenv("GUARDIAN_API_KEY")
    today_date = (datetime.today()-timedelta(days=1)).strftime("%Y-%m-%d")
    #time.strftime("%Y-%m-%d")-

    client = BaseClient(base_url=config.BASE_URL, api_key=api_key)
    
    params = {
        'from-date': today_date,
        'to-date': today_date,
        'show-fields': 'bodyText,headline,publication', # Request full content text
        'page-size': 10, # Max allowed page size
        'q': "", # Optional search query
        'order-by': 'newest',
        'page': 1 # Start at page 1
    }
    # request with exception handling for both response and requests
    try:
        response = client.get_all_articles(params=params)
    except errors.APITimeoutError as e:
        print(f"Timeout error: {e}")
    except errors.APIAuthError as e:
        print(f"Auth error: {e}")
    except errors.APIClientError as e:
        print(f"Client error: {e}")
    except errors.APIServerError as e:
        print(f"Server error: {e}")
    except errors.APIBaseError as e:
        print(f"Unexpected error: {e}")
    
    
    
    
    
    
    
    
if __name__ == "__main__":
    main()
    
    
    