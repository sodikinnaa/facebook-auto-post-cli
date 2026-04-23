
from datetime import datetime
activate = False

def response_template(status, message, data=None, meta=None):
	if not activate:
		return {
            'status': status,
            'message': message,
            'data': data if data is not None else [],
            'meta': meta if meta is not None else {},
        }
	return {
		'status': status,
		'message': message,
		'data': data if data is not None else [],
		'meta': meta if meta is not None else {},
		'timestamp': datetime.now().isoformat(),
		'version': '1.0',
	}
