# anytoggl/http.py
import httpx
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt

RETRY = retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
