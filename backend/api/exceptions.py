import logging
import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

GENERIC_SERVER_ERROR = 'An unexpected error occurred.'


def _coerce_to_list(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return {key: _coerce_to_list(item) for key, item in value.items()}
    return [str(value)]



def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.error('Unhandled exception in %s:\n%s', context.get('view'), traceback.format_exc())
        return Response(
            {
                'detail': GENERIC_SERVER_ERROR,
                'errors': {'non_field_errors': [GENERIC_SERVER_ERROR]},
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    detail = 'Request error'
    errors = {}

    if isinstance(data, dict):
        if 'detail' in data:
            detail = str(data['detail'])
            errors['non_field_errors'] = [detail]
        for key, value in data.items():
            if key == 'detail':
                continue
            errors[key] = _coerce_to_list(value)
        if not errors:
            errors['non_field_errors'] = [detail]
        elif response.status_code >= 500:
            detail = GENERIC_SERVER_ERROR
    elif isinstance(data, list):
        detail = 'Validation error'
        errors['non_field_errors'] = _coerce_to_list(data)
    else:
        detail = str(data)
        errors['non_field_errors'] = [detail]

    response.data = {
        'detail': detail,
        'errors': errors,
        'status_code': response.status_code,
    }
    return response
