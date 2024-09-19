from typing import Generator


def _get_subclasses[T: type](cls: T) -> Generator[T, None, None]:
    subs = cls.__subclasses__()
    yield from subs
    for sub in subs:
        yield from get_subclasses(sub)


def get_subclasses[T: type](cls: T) -> list[T]:
    return list(_get_subclasses(cls))
