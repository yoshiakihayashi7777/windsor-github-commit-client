from dataclasses import dataclass


@dataclass(frozen=True)
class Commit:
    sha: str
    author_name: str | None
    author_email: str | None
    date: str | None
    message: str