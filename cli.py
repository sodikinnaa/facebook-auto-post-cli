from datetime import datetime, UTC
import json

from api.backend import SociamediaPostBackend
from api.config.app import BEARER_SOCIAL_MEDIA_POST, ENDPOINT_SOCIAL_MEDIA_POST, SHEET_ID
from api.db_sheet import SheetDB


sheet_db = SheetDB()
backend = SociamediaPostBackend()


def _print_json(data):
	print(json.dumps(data, indent=4, ensure_ascii=False))


def check_env_config():
	env_info = {
		'BEARER_SOCIAL_MEDIA_POST_set': bool(BEARER_SOCIAL_MEDIA_POST),
		'ENDPOINT_SOCIAL_MEDIA_POST': ENDPOINT_SOCIAL_MEDIA_POST,
		'SHEET_ID': SHEET_ID,
		'credential_path': str(sheet_db._get_credential_path()),
	}

	response = {
		'status': 'success',
		'message': 'Ringkasan konfigurasi env',
		'data': env_info,
	}
	_print_json(response)


def list_draft_content():
	draft_response = sheet_db.getDraftContentData()
	_print_json(draft_response)


def _extract_publish_fields(response_data):
	if not isinstance(response_data, dict):
		return '', ''

	# Backend kadang mengembalikan payload publish di data.data
	result_data = response_data.get('data')
	if isinstance(result_data, dict):
		payload = result_data
	else:
		payload = response_data

	platform_post_id = (
		payload.get('facebook_post_id')
		or payload.get('post_id')
		or payload.get('id')
		or ''
	)
	published_url = (
		payload.get('facebook_post_url')
		or payload.get('url')
		or payload.get('post_url')
		or payload.get('permalink_url')
		or ''
	)

	published_url = _normalize_public_facebook_url(str(published_url).strip())
	return str(platform_post_id), published_url


def _normalize_public_facebook_url(url):
	if not url:
		return ''

	if url.startswith('https://'):
		return url

	if url.startswith('/'):
		return f'https://www.facebook.com{url}'

	return f'https://www.facebook.com/{url.lstrip("/")}'


def _normalize_bool(value):
	if isinstance(value, bool):
		return value

	raw = str(value).strip().lower()
	if raw in ('true', '1', 'yes', 'y', 'on'):
		return True
	if raw in ('false', '0', 'no', 'n', 'off', ''):
		return False
	return False


def publish_draft_content():
	draft_response = sheet_db.getDraftContentData()
	if draft_response.get('status') != 'success':
		_print_json(draft_response)
		return

	drafts = draft_response.get('data', [])
	if not drafts:
		_print_json(
			{
				'status': 'success',
				'message': 'Tidak ada data draft untuk dipublish',
				'data': [],
				'meta': {'record_count': 0},
			}
		)
		return

	results = []
	for row in drafts:
		row_number = row.get('_row_number')
		is_dry_run = _normalize_bool(row.get('dry_run', ''))
		post_result = backend.send_post(row)

		is_success = post_result.get('status') == 'success'
		post_data = post_result.get('data')
		platform_post_id, published_url = _extract_publish_fields(post_data)

		now_utc = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
		if is_success and is_dry_run:
			new_status = 'draft'
			tanggal_publish = ''
		else:
			new_status = 'published' if is_success else 'failed'
			tanggal_publish = now_utc if is_success else ''

		update_payload = {
			'status': new_status,
			'tanggal_publish': tanggal_publish,
			'url_publish': published_url,
			'post_url': published_url,
			'platform_post_id': platform_post_id,
			'publish_response': post_data,
			'last_error': '' if is_success else post_result.get('message', 'Publish gagal'),
			'updated_at': now_utc,
		}

		update_result = sheet_db.updateStatusAfterPublish(int(row_number), update_payload)

		results.append(
			{
				'row_number': row_number,
				'post_id': row.get('post_id', ''),
				'is_dry_run': is_dry_run,
				'publish_status': post_result.get('status'),
				'publish_message': post_result.get('message'),
				'sheet_status_set_to': new_status,
				'sheet_update_status': update_result.get('status'),
				'sheet_update_message': update_result.get('message'),
			}
		)

	_print_json(
		{
			'status': 'success',
			'message': 'Proses publish draft selesai',
			'data': results,
			'meta': {
				'total': len(results),
				'success_count': len([r for r in results if r['publish_status'] == 'success']),
				'failed_count': len([r for r in results if r['publish_status'] != 'success']),
			},
		}
	)



def main():
	while True:
		print('\n=== Social Media Posting CLI ===')
		print('1. Cek file env')
		print('2. List content draft')
		print('3. Posting ke social media')
		print('q. Exit')

		choice = input('Pilih menu (1-3): ').strip()

		if choice == '1':
			check_env_config()
		elif choice == '2':
			list_draft_content()
		elif choice == '3':
			publish_draft_content()
		elif choice == 'q':
			print('Selesai.')
			break
		else:
			print('Pilihan tidak valid. Gunakan 1, 2, 3, atau q.')


if __name__ == '__main__':
	main()