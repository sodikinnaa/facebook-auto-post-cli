from pathlib import Path
import os
import sys


def _get_runtime_base_dir():
	if getattr(sys, 'frozen', False):
		return Path(sys.executable).resolve().parent
	return Path(__file__).resolve().parent.parent.parent


BASE_DIR = _get_runtime_base_dir()


def _load_dotenv():
	candidate_paths = [
		BASE_DIR / '.env',
		Path.cwd() / '.env',
	]

	for env_path in candidate_paths:
		if env_path.exists():
			break
	else:
		return

	for raw_line in env_path.read_text(encoding='utf-8').splitlines():
		line = raw_line.strip()
		if not line or line.startswith('#') or '=' not in line:
			continue

		key, value = line.split('=', 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")

		if key and key not in os.environ:
			os.environ[key] = value


_load_dotenv()

BEARER_TOKEN = os.getenv('BEARER_TOKEN', '')
PAGE_ID = os.getenv('PAGE_ID', '')
PAGE_TOKEN = os.getenv('PAGE_TOKEN', '')
FB_GRAPH_API_VERSION = os.getenv('FB_GRAPH_API_VERSION', 'v20.0')
OPENAI_API_URL = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')


def get_auth_config():
	return {
		'bearer_token': BEARER_TOKEN,
	}


def get_openai_config():
	return {
		'api_url': OPENAI_API_URL,
		'api_key': OPENAI_API_KEY,
	}


def get_facebook_config():
	return {
		'page_id': PAGE_ID,
		'page_token': PAGE_TOKEN,
		'graph_api_version': FB_GRAPH_API_VERSION,
	}


