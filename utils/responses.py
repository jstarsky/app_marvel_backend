from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler

def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Standard success response format.

    If `message` is None the response will omit the `message` key so clients
    can rely on the HTTP status code and `success` flag. Callers can still
    provide a message when useful.
    """
    response_data = {
        "success": True,
        "data": data
    }

    if message is not None:
        response_data["message"] = message

    return Response(response_data, status=status_code)

def error_response(message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standard error response format
    """
    response_data = {
        "success": False,
        "message": message,
    }
    
    if errors:
        response_data["errors"] = errors
    
    return Response(response_data, status=status_code)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            "success": False,
            "message": "An error occurred",
            "errors": response.data
        }
        response.data = custom_response_data
    
    return response