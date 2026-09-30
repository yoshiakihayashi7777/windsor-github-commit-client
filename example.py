from github_client import GitHubClient


def main() -> None:
    client = GitHubClient()

    for commit in client.iter_commits(
        "torvalds",
        "linux",
        pages=3,
        per_page=100,
    ):
        first_line = commit.message.splitlines()[0]

        print(
            f"{commit.sha[:12]} | "
            f"{commit.author_name} | "
            f"{first_line}"
        )


if __name__ == "__main__":
    main()