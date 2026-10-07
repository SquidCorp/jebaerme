"""Process entry. No business logic."""

from jebaerme.services import get_health


def main() -> None:
    print(get_health().model_dump_json())


if __name__ == "__main__":
    main()
