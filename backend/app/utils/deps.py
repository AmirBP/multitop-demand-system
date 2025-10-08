from fastapi import Query

def pagination_params(page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=500)):
    return {"page": page, "size": size}
