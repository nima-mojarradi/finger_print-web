import json
import logging

logger = logging.getLogger('core')


def log_to_elasticsearch(log_data, log_level='info'):
    if log_level == 'info':
        logger.info(json.dumps(log_data))
    elif log_level == 'error':
        logger.error(json.dumps(log_data))


def log_format(request, response=None, exception=None):
    user = getattr(request, 'user', None)
    user_id = getattr(user, 'id', None)
    user_info = {
        'user_id': user_id,
        'user_username': getattr(user, 'username', ' '),
        'user_email': getattr(user, 'email', ' '),
        'user_phone': getattr(user, 'phone_number', ' '),
    }

    remote_host = request.META.get("REMOTE_ADDR", '-')
    request_line = f"{request.method} {request.get_full_path()}"
    status_code = response.status_code if response else 500
    response_size = response.get('Content-Length', ' ') if response else ' '
    referrer = request.META.get('HTTP_REFERER', '-')
    user_agent = request.headers.get("user-agent", '-')
    event = request.get_full_path()
    message = str(exception) if exception else 'Request successfully'

    return {
        'user_info': user_info,
        'remote_host': remote_host,
        'request_line': request_line,
        'status_code': status_code,
        'response_size': response_size,
        'referrer': referrer,
        'user_agent': user_agent,
        'event': event,
        'message': message,
    }


def authentication_log_format(user, body, exception=None):
    message = str(exception) if exception else 'Consume successfully'
    return {
        'user_id': str(user.id),
        'user_phone': str(getattr(user, 'phone', '')),
        'user_agent': body.get("user_agent"),
        'event': f"consumer.{body.get('routing_key')}",
        "status": "success",
        'message': message
    }


def rss_log_format(body, exception=None):
    message = str(exception) if exception else 'Consume successfully'
    return {
        'event': f"consumer.{body.get('routing_key')}",
        "status": "success",
        'message': message
    }
