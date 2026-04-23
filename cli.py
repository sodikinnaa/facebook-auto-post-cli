from api.backend import SociamediaPostBackend
from api.db_sheet import SheetDB
import json 

sheet_db = SheetDB()

# get data from google sheet
sheet_response = sheet_db.getSheetData()
print(json.dumps(sheet_response))