import gspread
from oauth2client.service_account import ServiceAccountCredentials

def tester():

	scope = ['https://spreadsheets.google.com/feeds']
	creds = ServiceAccountCredentials.from_json_keyfile_name('key2.json', scope)
	gc = gspread.authorize(creds)
	wks = gc.open_by_url("https://docs.google.com/spreadsheets/d/1wiwqmIbEuwCFt4E69ab_-oDAxnL11MOykmnHkCRGFNI").sheet1
	wks.update_acell('B2', "Hello")

def main():
	tester()

main()
