from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging
logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        msg = response.data
        if isinstance(msg, dict):
            msg = next((str(v[0]) if isinstance(v,list) else str(v) for v in msg.values()), str(response.data))
        elif isinstance(msg, list):
            msg = str(msg[0])
        else:
            msg = str(msg)
        response.data = {'error': True, 'code': getattr(exc,'default_code','error'), 'message': msg, 'detail': response.data}
    else:
        logger.exception(f"Unhandled: {context.get('view')}")
        response = Response({'error':True,'code':'internal_error','message':'An unexpected error occurred.'}, status=500)
    return response
