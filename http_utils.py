import requests
import time
from logger_config import logger

def get_with_retry(url,params=None,headers=None,timeout=10,retries=3):
    return request_with_retry(
        method="GET",
        url=url,
        params=params,
        headers=headers,
        timeout=timeout,
        retries=retries
    )

def post_with_retry(url,headers=None,data=None,json_data=None,timeout=10,retries=3):
    return request_with_retry(
        method="POST",
        url=url,
        headers=headers,
        data=data,
        json_data=json_data,
        timeout=timeout,
        retries=retries
    )

def request_with_retry(
        method,
        url,
        params=None,
        headers=None,
        data=None,
        json_data=None,
        timeout=10,
        retries=3):
    for attempt in range(retries):
        try:    
            response=requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout,
                headers=headers
            )
            status=response.status_code
            if 200<=status<300:
                return response
            
            logger.error(
                f"接口返回错误 "
                f"url={url} "
                f"attempt={attempt + 1} "
                f"status={status} "
                f"body={response.text}"
            )

            if 400 <= status < 500 and status != 429:
                response.raise_for_status()

            if status == 429 or status >= 500:
                if attempt == retries - 1:
                    response.raise_for_status()

                retry_wait(attempt)
                continue

            response.raise_for_status()
        
        except requests.Timeout as e:
            logger.error(
                f"请求超时，method={method}"
                f"url={url},attempt={attempt+1}/{retries},error={e}"
            )
            if attempt==retries-1:
                raise
            retry_wait(attempt)
        except requests.HTTPError as e:
                raise
        except requests.RequestException:
            logger.error(
                f"网络异常"
            )            
            if attempt == retries-1:
                raise
            retry_wait(attempt)
            
def retry_wait(attempt):
    wait_time=2**attempt

    logger.info(
        f"等待重试 wait={wait_time}"
    )
    time.sleep(wait_time)
