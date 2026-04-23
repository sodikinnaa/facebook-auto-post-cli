from api.db_sheet import SheetDB
import json 

sheet_db = SheetDB()

# get data from google sheet
sheet_response = sheet_db.getSheetData()
draft_data = sheet_db.getDraftContentData()

print('draft data:')
print(json.dumps(draft_data, indent=4))
print('data sheet response:')
# print(json.dumps(sheet_response, indent=4))