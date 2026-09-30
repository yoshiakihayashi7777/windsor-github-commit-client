from unittest.mock import Mock

import pytest
import requests

from github_client import GitHubClient, GitHubClientError


def make_response(
    status_code: int,
    payload,
    *,
    headers: dict[str, str] | None = None,
    text: str = "",
) -> Mock:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.ok = 200 <= status_code < 400
    response.headers = headers or {}
    response.text = text
    response.json.return_value = payload

    return response


def test_paginates_and_normalizes_commits() -> None:
    session = Mock()
    session.headers = {}

    session.get.side_effect = [
        make_response(
            200,
            [
                {
                    "sha": "commit-one",
                    "commit": {
                        "author": {
                            "name": "Ada Lovelace",
                            "email": "ada@example.com",
                            "date": "2026-01-01T00:00:00Z",
                        },
                        "message": "Add first change",
                    },
                }
            ],
        ),
        make_response(
            200,
            [
                {
                    "sha": "commit-two",
                    "commit": {
                        "author": {
                            "name": "Grace Hopper",
                            "email": "grace@example.com",
                            "date": "2026-01-02T00:00:00Z",
                        },
                        "message": "Add second change",
                    },
                }
            ],
        ),
    ]

    client = GitHubClient(session=session)

    commits = list(
        client.iter_commits(
            "torvalds",
            "linux",
            pages=2,
            per_page=1,
        )
    )

    assert len(commits) == 2
    assert commits[0].sha == "commit-one"
    assert commits[0].author_name == "Ada Lovelace"
    assert commits[0].author_email == "ada@example.com"
    assert commits[1].message == "Add second change"

    assert session.get.call_args_list[0].kwargs["params"] == {
        "page": 1,
        "per_page": 1,
    }

    assert session.get.call_args_list[1].kwargs["params"] == {
        "page": 2,
        "per_page": 1,
    }


def test_retries_rate_limit_response() -> None:
    session = Mock()
    session.headers = {}

    session.get.side_effect = [
        make_response(
            403,
            {},
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1000",
            },
            text="API rate limit exceeded",
        ),
        make_response(200, []),
    ]

    sleep = Mock()

    client = GitHubClient(
        session=session,
        sleep=sleep,
    )

    commits = list(
        client.iter_commits(
            "torvalds",
            "linux",
            pages=1,
        )
    )

    assert commits == []
    sleep.assert_called_once()
    assert session.get.call_count == 2


def test_does_not_retry_normal_forbidden_response() -> None:
    session = Mock()
    session.headers = {}

    session.get.return_value = make_response(
        403,
        {},
        headers={
            "X-RateLimit-Remaining": "10",
        },
        text="Forbidden",
    )

    client = GitHubClient(session=session)

    with pytest.raises(GitHubClientError):
        list(
            client.iter_commits(
                "torvalds",
                "linux",
                pages=1,
            )
        )

    assert session.get.call_count == 1