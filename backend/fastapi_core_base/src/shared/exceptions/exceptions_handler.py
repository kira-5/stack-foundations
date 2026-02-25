# exception_handler.py

from src.shared.configuration import constants as core_constants
from src.shared.configuration import response
from src.shared.exceptions.exception import BusinessCaseException, TechnicalException
from fastapi import FastAPI, Request


async def business_case_exception_handler(request: Request, exc: BusinessCaseException):
    user_id = (
        request.state.user_id if request and hasattr(request.state, "user_id") else None
    )

    # Use the status_code and message from the exception
    status_code = exc.status_code
    message = exc.message
    data = exc.data

    # Create error summary with extracted details
    details = str(exc).splitlines()

    # Join multiple lines into a single string if there are multiple details
    detail_formatted = "\n".join(details) if len(details) > 1 else details[0]

    error_summary = {
        "type": type(exc).__name__,
        "detail": detail_formatted,
        # Uncomment if you want to include traceback information
        # "traceback": traceback.format_exc().splitlines(),
        # "file_line_info": [
        #     line for line in traceback.format_exc().splitlines() if "File" in line
        # ],
    }

    return response.BaseJSONResponse(
        status=status_code,
        success=core_constants.FAILURE_FLAG,
        user_id=user_id,
        message=message,
        data=data or [],
        error=error_summary,
    )


# async def technical_exception_handler(request: Request, exc: TechnicalException):
#     user_id = (
#         request.state.user_id if request and hasattr(request.state, "user_id") else None
#     )

#     # Create error summary with extracted details
#     details = str(exc).splitlines()

#     # Join multiple lines into a single string if there are multiple details
#     detail_formatted = "\n".join(details) if len(details) > 1 else details[0]

#     error_summary = {
#         "type": type(exc).__name__,
#         "detail": detail_formatted,
#         # Uncomment if you want to include traceback information
#         # "traceback": traceback.format_exc().splitlines(),
#         # "file_line_info": [
#         #     line for line in traceback.format_exc().splitlines() if "File" in line
#         # ],
#     }

#     return response.BaseJSONResponse(
#         status=core_constants.STATUS_ERROR,
#         success=core_constants.FAILURE_FLAG,
#         user_id=user_id,
#         message=core_constants.ERROR_MESSAGE,
#         data=[],
#         error=error_summary,
#     )


async def technical_exception_handler(request: Request, exc: Exception):
    # user_id = (
    #     request.state.user_id if request and hasattr(request.state, "user_id") else None
    # )

    # # Determine if exc is a TechnicalException or a string
    # if isinstance(exc, TechnicalException):
    #     # Create error summary with extracted details from TechnicalException
    #     details = str(exc).splitlines()
    #     detail_formatted = "\n".join(details) if len(details) > 1 else details[0]

    #     error_summary = {
    #         "type": type(exc).__name__,
    #         "detail": detail_formatted,
    #         # Uncomment if you want to include traceback information
    #         # "traceback": traceback.format_exc().splitlines(),
    #         # "file_line_info": [
    #         #     line for line in traceback.format_exc().splitlines() if "File" in line
    #         # ],
    #     }
    # else:
    #     # Handle the case where exc is a string
    #     error_summary = {
    #         "type": "GenericError",
    #         "detail": exc,  # Use the string directly
    #     }

    user_id = (
        request.state.user_id if request and hasattr(request.state, "user_id") else None
    )

    # Create an error summary
    error_summary = {
        "type": type(exc).__name__,
        "detail": str(exc),  # Directly use the string representation of the exception
    }

    return response.BaseJSONResponse(
        status=core_constants.STATUS_ERROR,
        success=core_constants.FAILURE_FLAG,
        user_id=user_id,
        message=core_constants.ERROR_MESSAGE,
        data=[],
        error=error_summary,
    )


def add_exception_handlers(app: FastAPI):
    """Adds exception handlers to the FastAPI app."""
    app.add_exception_handler(BusinessCaseException, business_case_exception_handler)
    app.add_exception_handler(TechnicalException, technical_exception_handler)
