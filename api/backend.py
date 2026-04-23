from api.config.app import BEARER_SOCIAL_MEDIA_POST, ENDPOINT_SOCIAL_MEDIA_POST
from api.response.response_template import response_template
import requests

class SociamediaPostBackend:
    def __init__(self):
        self.bearer_token = BEARER_SOCIAL_MEDIA_POST
        self.endpoint = ENDPOINT_SOCIAL_MEDIA_POST

    def send_post(self, post_data): 
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(self.endpoint, json=post_data, headers=headers)
            response.raise_for_status()
            return response_template('success', 'Post sent successfully', data=response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error sending post: {e}")
            return response_template('error', 'Failed to send post', data=str(e))