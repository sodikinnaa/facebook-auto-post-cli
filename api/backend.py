import requests
from api.config.app import BEARER_SOCIAL_MEDIA_POST, ENDPOINT_SOCIAL_MEDIA_POST
from api.response.response_template import response_template

class SociamediaPostBackend:
    def __init__(self):
        self.bearer_token = BEARER_SOCIAL_MEDIA_POST
        self.endpoint = self._normalize_endpoint(ENDPOINT_SOCIAL_MEDIA_POST)

    def send_post(self, post_data):
        if not isinstance(post_data, dict):
            return response_template('error', 'post_data harus berupa object/dict', data={})

        page_id = str(post_data.get('page_id', '')).strip()
        # Token wajib diambil dari data sheet, bukan dari environment.
        credential = str(
            post_data.get('credential', '')
            or post_data.get('page_token', '')
            or post_data.get('credential_key', '')
        ).strip()

        if not page_id:
            return response_template('error', 'Field page_id wajib ada di data sheet', data=post_data)

        if not credential:
            return response_template('error', 'Field token wajib ada di data sheet (credential/page_token/credential_key)', data=post_data)

        payload = {
            'message': post_data.get('message', ''),
            'request_id': post_data.get('request_id', ''),
        }

        image_urls = self._normalize_image_urls(post_data.get('image_urls'))
        if image_urls:
            payload['image_urls'] = image_urls
        if post_data.get('video_url'):
            payload['video_url'] = post_data.get('video_url')
        if str(post_data.get('dry_run', '')).strip() != '':
            payload['dry_run'] = self._normalize_bool(post_data.get('dry_run'))

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json',
        }

        params = {
            'page_id': page_id,
            'credential': credential,
        }

        try:
            response = requests.post(self.endpoint, params=params, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response_template('success', 'Post sent successfully', data=response.json())
        except requests.exceptions.RequestException as e:
            detail = self._extract_error_detail(e)
            return response_template('error', 'Failed to send post', data=detail)

    def _normalize_image_urls(self, image_urls):
        if not image_urls:
            return []

        if isinstance(image_urls, list):
            return [str(url).strip() for url in image_urls if str(url).strip()]

        raw_urls = str(image_urls).strip()
        if not raw_urls:
            return []

        # Format di sheet dipisahkan dengan titik koma (;)
        if ';' in raw_urls:
            return [url.strip() for url in raw_urls.split(';') if url.strip()]

        return [raw_urls]

    def _normalize_bool(self, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        raw = str(value).strip().lower()
        if raw in ('true', '1', 'yes', 'y', 'on'):
            return True
        if raw in ('false', '0', 'no', 'n', 'off', ''):
            return False

        # Fallback aman: nilai tak dikenal dianggap False untuk hindari dry_run tak sengaja aktif.
        return False

    def _normalize_endpoint(self, endpoint):
        raw_endpoint = str(endpoint or '').strip().rstrip('/')
        if not raw_endpoint:
            return ''

        publish_path = '/api/v1/facebook/publish'
        if raw_endpoint.endswith(publish_path):
            return raw_endpoint

        return f'{raw_endpoint}{publish_path}'

    def _extract_error_detail(self, err):
        response = getattr(err, 'response', None)
        if response is None:
            return str(err)

        response_text = ''
        try:
            response_text = response.text
        except Exception:
            response_text = ''

        if response_text:
            return f'{response.status_code} {response.reason}: {response_text}'

        return str(err)