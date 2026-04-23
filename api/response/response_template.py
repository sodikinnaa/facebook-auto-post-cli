
from datetime import datetime

def response_template(status, message, data=None, meta=None):
	
	return {
		'status': status,
		'message': message,
		'data': data if data is not None else [],
		'meta': meta if meta is not None else {},
		'timestamp': datetime.now().isoformat(),
		'version': '1.0',
	}
