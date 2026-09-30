from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from typing import Any

import requests

from .models import Commit


class GitHubClientError(RuntimeError):
    """Raised when GitHub cannot provide a successful response."""


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        *,
        token: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        sleep: Any = time.sleep,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.sleep = sleep

        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def iter_commits(
        self,
        owner: str,
        repo: str,
        *,
        pages: int = 5,
        per_page: int = 100,
    ) -> Iterator[Commit]:
        if pages < 1:
            raise ValueError("pages must be at least 1")

        if not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")

        endpoint = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"

        for page in range(1, pages + 1):
            response = self._get(
                endpoint,
                params={
                    "page": page,
                    "per_page": per_page,
                },
            )

            payload = response.json()

            if not isinstance(payload, list):
                raise GitHubClientError(
                    "GitHub returned an unexpected response format"
                )

            for raw_commit in payload:
                yield self.normalize_commit(raw_commit)

    @staticmethod
    def normalize_commit(raw_commit: Mapping[str, Any]) -> Commit:
        commit_data = raw_commit.get("commit") or {}
        author = commit_data.get("author") or {}

        return Commit(
            sha=str(raw_commit.get("sha", "")),
            author_name=author.get("name"),
            author_email=author.get("email"),
            date=author.get("date"),
            message=str(commit_data.get("message", "")),
        )

    def _get(
        self,
        url: str,
        *,
        params: Mapping[str, Any],
    ) -> requests.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise GitHubClientError(
                        "GitHub request failed after retries"
                    ) from exc

                self.sleep(2**attempt)
                continue

            if response.ok:
                return response

            if self._is_rate_limited(response):
                if attempt < self.max_retries:
                    self.sleep(self._retry_delay(response, attempt))
                    continue

            raise GitHubClientError(
                f"GitHub returned HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )

        raise GitHubClientError("GitHub request failed after retries")

    @staticmethod
    def _is_rate_limited(response: requests.Response) -> bool:
        remaining = response.headers.get("X-RateLimit-Remaining")

        return response.status_code == 403 and (
            remaining == "0"
            or "rate limit" in response.text.lower()
        )

    def _retry_delay(
        self,
        response: requests.Response,
        attempt: int,
    ) -> float:
        reset_timestamp = response.headers.get("X-RateLimit-Reset")

        if (
            reset_timestamp
            and response.headers.get("X-RateLimit-Remaining") == "0"
        ):
            try:
                seconds_until_reset = float(reset_timestamp) - time.time()
                return max(0.0, seconds_until_reset)
            except ValueError:
                pass

        return min(2**attempt, 30.0)