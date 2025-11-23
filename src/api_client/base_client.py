import logging
import time
import random
from typing import Dict, Any, Generator, Optional, List
import logging
import requests
import src.api_client.config as config
import os
from dotenv import load_dotenv
import requests
import src.api_client.errors as errors

class BaseClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 20) -> None:
        self.base_url = config.BASE_URL
        self.timeout = config.DEFAULT_TIMEOUT
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key


    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        
        url = f"{self.base_url}{endpoint}"
        session = requests.Session()
        
        params["api-key"] = self.api_key
        if params is None:
            params = {}
        
        self.logger.debug("Making %s request to %s with params %s", method, url, params)

        # HTTP request - handling errors, raised to be captured by caller
        try:
            resp = session.request(method, url, params=params, timeout=self.timeout)
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

def main():
    load_dotenv()
    # TODO: change to get_env utility function
    api_key = os.getenv("GUARDIAN_API_KEY")
    
    client = BaseClient(base_url=config.BASE_URL, api_key=api_key)
    
    # request with exception handling for both response and requests
    try:
        response = client._request("GET", "/search", {"q": "test"})
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
    
    
    