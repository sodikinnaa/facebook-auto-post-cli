import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
import json
from api.config.app import SHEET_ID
from api.response.response_template import response_template

class SheetDB:
    def __init__(self, sheet_name='Content', sheet_key=None):
        self.sheet_name = sheet_name
        self.sheet_key = sheet_key or SHEET_ID
        self.content_columns = [
            'post_id',
            'source_ref',
            'content_type',
            'message',
            'image_urls',
            'video_url',
            'video_file_path',
            'request_id',
            'dry_run',
            'page_id',
            'credential_key',
            'status',
            'tanggal_publish',
            'url_publish',
            'platform_post_id',
            'publish_response',
            'last_error',
            'created_at',
            'updated_at',
        ]

    def _get_credential_path(self):
        base_dir = Path(__file__).resolve().parent.parent / 'credentials'
        candidates = [
            base_dir / 'sheet' / 'user_credential.json',
            base_dir / 'user_credential.json',
        ]

        for path in candidates:
            if path.exists():
                return path

        return candidates[0]

    def getSheetData(self):
        credential_path = self._get_credential_path()

        if not credential_path.exists():
            return response_template(
                status='error',
                message=f'Credential file tidak ditemukan: {credential_path}',
                data=[],
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                },
            )

        try:
            sheet = self._get_sheet_instance(credential_path)
            records = sheet.get_all_records()

            return response_template(
                status='success',
                message='Data sheet berhasil diambil',
                data=records,
                meta={
                    'sheet_name': self.sheet_name,
                    'record_count': len(records),
                },
            )
        except Exception as err:
            return response_template(
                status='error',
                message=str(err),
                data=[],
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                },
            )

    def _get_sheet_instance(self, credential_path):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credits = ServiceAccountCredentials.from_json_keyfile_name(str(credential_path), scope)
        client = gspread.authorize(credits)
        return client.open_by_key(self.sheet_key).worksheet(self.sheet_name)

    def checkDbConnection(self):
        credential_path = self._get_credential_path()

        if not credential_path.exists():
            return response_template(
                status='error',
                message=f'Credential file tidak ditemukan: {credential_path}',
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                    'connected': False,
                },
            )

        try:
            sheet = self._get_sheet_instance(credential_path)
            worksheet_title = getattr(sheet, 'title', '')

            return response_template(
                status='success',
                message='Koneksi ke Google Sheet berhasil',
                data={
                    'worksheet_title': worksheet_title,
                },
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                    'connected': True,
                },
            )
        except Exception as err:
            return response_template(
                status='error',
                message=str(err),
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                    'connected': False,
                },
            )

    # ambil content status draft yang belum diproses (status kosong atau draft)
    def getDraftContentData(self):
        credential_path = self._get_credential_path()

        if not credential_path.exists():
            return response_template(
                status='error',
                message=f'Credential file tidak ditemukan: {credential_path}',
                data=[],
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                },
            )

        try:
            sheet = self._get_sheet_instance(credential_path)
            rows = sheet.get_all_values()

            if not rows:
                return response_template(
                    status='success',
                    message='Sheet kosong',
                    data=[],
                    meta={
                        'sheet_name': self.sheet_name,
                        'record_count': 0,
                    },
                )

            headers = rows[0]
            status_index = headers.index('status') if 'status' in headers else -1

            filtered_rows = []
            for row_number, row_values in enumerate(rows[1:], start=2):
                row_data = {
                    header: row_values[idx] if idx < len(row_values) else ''
                    for idx, header in enumerate(headers)
                }

                status_value = ''
                if status_index >= 0 and status_index < len(row_values):
                    status_value = str(row_values[status_index]).strip().lower()

                if status_value in ('', 'draft'):
                    row_data['_row_number'] = row_number
                    filtered_rows.append(row_data)

            return response_template(
                status='success',
                message='Data draft berhasil diambil',
                data=filtered_rows,
                meta={
                    'sheet_name': self.sheet_name,
                    'record_count': len(filtered_rows),
                },
            )
        except Exception as err:
            return response_template(
                status='error',
                message=str(err),
                data=[],
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                },
            )

    # update status content and antoher after publish content
    