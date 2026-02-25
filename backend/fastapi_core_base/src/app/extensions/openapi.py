from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    # Remove error 422 from schema if present
    def remove_422(openapi_dict):
        for k, v in openapi_dict.items():
            if isinstance(v, dict) and "422" in v.keys():
                del v["422"]
                break
            elif isinstance(v, dict):
                remove_422(v)
        return openapi_dict

    openapi_schema = remove_422(openapi_schema)
    app.openapi_schema = openapi_schema
    return app.openapi_schema
