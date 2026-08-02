import json
import socket
import ssl
import time
import urllib.error
import urllib.request

from .errors import ApiError


class Client:
    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
    TRANSIENT_ERRORS = (
        EOFError,
        ConnectionResetError,
        ConnectionRefusedError,
        TimeoutError,
        ssl.SSLError,
        socket.gaierror,
        urllib.error.URLError,
    )
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def __init__(self, builder):
        self.builder = builder

    def call(self, max_output_tokens=1024):
        payload = json.dumps(
            self.builder.to_api_payload(max_output_tokens=max_output_tokens)
        ).encode("utf-8")
        request = urllib.request.Request(
            self.builder.url(),
            data=payload,
            headers=self.builder.headers(),
            method="POST",
        )

        attempts = 0
        response_code = None
        response_body = None

        while True:
            attempts += 1

            try:
                with urllib.request.urlopen(request) as response:
                    response_code = response.status
                    response_body = response.read()
            except urllib.error.HTTPError as e:
                response_code = e.code
                response_body = e.read()
            except self.TRANSIENT_ERRORS as e:
                if attempts > self.MAX_RETRIES:
                    raise ApiError(
                        f"API request failed after {attempts} attempts: {type(e).__name__}: {e}"
                    ) from e

                time.sleep(self._retry_delay(attempts))
                continue

            if self._retryable_response(response_code) and attempts <= self.MAX_RETRIES:
                time.sleep(self._retry_delay(attempts))
                continue

            break

        if not (200 <= response_code < 300):
            suffix = "" if attempts == 1 else "s"
            raise ApiError(
                f"API request failed after {attempts} attempt{suffix} "
                f"({response_code}): {response_body.decode('utf-8', errors='replace')}"
            )

        return json.loads(response_body)

    def _retryable_response(self, code):
        return code in self.RETRYABLE_STATUS_CODES

    def _retry_delay(self, attempt):
        return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
