from typing import Sequence, Any

def paginate(items: Sequence[Any], page: int, size: int):
    start = (page - 1) * size
    end = start + size
    return items[start:end], len(items)