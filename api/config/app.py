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

BEARER_SOCIAL_MEDIA_POST = os.getenv('BEARER_SOCIAL_MEDIA_POST', '')
ENDPOINT_SOCIAL_MEDIA_POST = os.getenv('ENDPOINT_SOCIAL_MEDIA_POST', '')


