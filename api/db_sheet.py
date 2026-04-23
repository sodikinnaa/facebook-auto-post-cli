import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
from datetime import datetime
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
    def updateStatusAfterPublish(self, row_number, payload):
        credential_path = self._get_credential_path()

        if not credential_path.exists():
            return response_template(
                status='error',
                message=f'Credential file tidak ditemukan: {credential_path}',
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                    'credential_path': str(credential_path),
                },
            )

        if not isinstance(row_number, int) or row_number < 2:
            return response_template(
                status='error',
                message='row_number harus integer dan minimal 2',
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                },
            )

        if not isinstance(payload, dict):
            return response_template(
                status='error',
                message='payload harus berupa object/dict',
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                },
            )

        updatable_fields = [
            'status',
            'tanggal_publish',
            'url_publish',
            'platform_post_id',
            'publish_response',
            'last_error',
            'updated_at',
        ]

        # updated_at otomatis diisi ketika caller belum mengirim nilai.
        data_to_update = {field: payload.get(field, '') for field in updatable_fields}
        if not str(data_to_update.get('updated_at', '')).strip():
            data_to_update['updated_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        # Simpan publish_response sebagai string agar aman disimpan di sel spreadsheet.
        if isinstance(data_to_update.get('publish_response'), (dict, list)):
            data_to_update['publish_response'] = json.dumps(data_to_update['publish_response'], ensure_ascii=False)

        try:
            sheet = self._get_sheet_instance(credential_path)
            headers = sheet.row_values(1)
            header_to_col_index = {header: idx + 1 for idx, header in enumerate(headers)}

            updated_fields = {}
            for field, value in data_to_update.items():
                col_index = header_to_col_index.get(field)
                if not col_index:
                    continue
                safe_value = '' if value is None else str(value)
                sheet.update_cell(row_number, col_index, safe_value)
                updated_fields[field] = safe_value

            if not updated_fields:
                return response_template(
                    status='error',
                    message='Tidak ada field yang bisa diupdate pada header sheet',
                    data={},
                    meta={
                        'sheet_name': self.sheet_name,
                        'row_number': row_number,
                    },
                )

            return response_template(
                status='success',
                message='Status publish berhasil diupdate',
                data={
                    'row_number': row_number,
                    'updated_fields': updated_fields,
                },
                meta={
                    'sheet_name': self.sheet_name,
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
                    'row_number': row_number,
                },
            )
    