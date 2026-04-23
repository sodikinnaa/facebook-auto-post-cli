import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
import json
from api.response.response_template import response_template

class SheetDB:
    def __init__(self, sheet_name='Content'):
        self.sheet_name = sheet_name
        self.content_columns = [
            'id-website',
            'topik',
            'tanggal_create',
            'target_audience',
            'category',
            'keyword',
            'judul',
            'meta_description',
            'aff_link',
            'content',
            'thumbnail_url',
            'status',
            'tanggal_publish',
            'url_publish',
        ]

    def _get_credential_path(self):
        base_dir = Path(__file__).resolve().parent.parent / 'credential'
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
        return client.open(self.sheet_name).sheet1

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

    def insertContentData(self, payload):
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

        if not isinstance(payload, dict):
            return response_template(
                status='error',
                message='Payload harus berupa object/dict',
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                },
            )

        row_data = {column: payload.get(column, '') for column in self.content_columns}

        try:
            sheet = self._get_sheet_instance(credential_path)
            sheet.append_row([row_data[column] for column in self.content_columns], value_input_option='USER_ENTERED')

            return response_template(
                status='success',
                message='Data berhasil ditambahkan ke sheet',
                data=row_data,
                meta={
                    'sheet_name': self.sheet_name,
                    'columns': self.content_columns,
                },
            )
        except Exception as err:
            return response_template(
                status='error',
                message=str(err),
                data={},
                meta={
                    'sheet_name': self.sheet_name,
                },
            )

    def insertCredential(self, credential_value):
        credential_path = self._get_credential_path()
        credential_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            parsed = json.loads(credential_value)
        except json.JSONDecodeError as err:
            return response_template(
                status='error',
                message=f'Format credential tidak valid: {err.msg}',
                data=[],
                meta={
                    'sheet_name': self.sheet_name,
                },
            )

        with open(credential_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        return response_template(
            status='success',
            message=f'Credential berhasil disimpan di {credential_path}',
            data={'credential_path': str(credential_path)},
            meta={
                'sheet_name': self.sheet_name,
            },
        )
    
    
