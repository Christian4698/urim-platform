from typing import Any


def walk_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        walked: list[Any] = []
        for nested_value in value.values():
            walked.extend(walk_values(nested_value))
        return walked

    if isinstance(value, list):
        walked = []
        for item in value:
            walked.extend(walk_values(item))
        return walked

    return [value]


def walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        walked = [str(key) for key in value]
        for nested_value in value.values():
            walked.extend(walk_keys(nested_value))
        return walked

    if isinstance(value, list):
        walked = []
        for item in value:
            walked.extend(walk_keys(item))
        return walked

    return []

