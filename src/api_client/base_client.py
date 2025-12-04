import logging
import time
from datetime import timedelta, datetime
import random
from typing import Dict, Any, Generator, Optional, List
import logging
import requests
import src.api_client.config as config
import os
from dotenv import load_dotenv
import requests
import src.api_client.errors as errors
import json

class BaseClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 20) -> None:
        self.base_url = config.BASE_URL
        self.timeout = config.DEFAULT_TIMEOUT
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.session = requests.Session()

    #TODO: implement generator, retries, backoff, jitter
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        
        url = f"{self.base_url}{endpoint}"
        #session = requests.Session()
        
        if params is None:
            params = {}        
        params["api-key"] = self.api_key

        
        self.logger.debug(f"Making {method} request to {url} with params {params}")

        # HTTP request - handling errors, raised to be captured by caller
        try:
            resp = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.Timeout as e:
            raise errors.APITimeoutError(f"Request timeout error {e}") from e
        except requests.RequestException as e:
            raise errors.APIConnectionError(f"Network error while calling {url}") from e
        
        status = resp.status_code
        
        # Response handling based on status codes
        if status == 200:
            return resp
        elif status == 401 or status == 403:
            raise errors.APIAuthError(f"Authentication error: {status}")
        elif 400 <= status< 500:
            raise errors.APIClientError(f"Rate limit exceeded: {status}")
        elif 500 <= status < 600:
            raise errors.APIServerError(f"Server error: {status}")
        else:
            raise errors.APIBaseError(f"Unexpected status code: {status}")

    def get_all_articles(self, params: Dict[str, Any]):
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
        


def main():
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
        print(len(response))
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
    
    
    