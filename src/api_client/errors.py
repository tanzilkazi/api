import logging
import time
import random
from typing import Dict, Any, Generator, Optional, List

class APIBaseError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        
class APIClientError(Exception):
    pass    

class APIServerError(Exception):
    pass
    
class APITimeoutError(Exception):
    pass
    
class APIAuthError(Exception):
    pass    
    
class APIConnectionError(Exception):
    pass
