import os
import html
import re
import datetime
import json

import requests
from dotenv import load_dotenv; load_dotenv()

from drive import sheets

SHEET_ID = os.environ.get('SHEET_ID')
def get_cookie():
    payload = {
        'login': os.environ.get('NYT_USERNAME'), 
        'password': os.environ.get('NYT_PASSWORD'),     
    }
            
    login_response = requests.post('https://myaccount.nytimes.com/svc/ios/v2/login', data=payload, headers={
        'User-Agent': 'Mozilla/5.0',
        'client_id': 'ios.crosswords',
    })
    login_response.raise_for_status()
    for cookie in login_response.json().get('data', {}).get('cookies', {}):
        if cookie.get('name') == 'NYT-S':
            return cookie.get('cipheredValue')

def get_rankings(): 
    login_cookie = get_cookie()
    leaderboard = requests.get("https://www.nytimes.com/puzzles/leaderboards", cookies={'NYT-S': login_cookie})
    
    data = re.search(r"window.data = ({.*?]})", html.unescape(leaderboard.text))
    entries = json.loads(data.group(1))
    
    ranking = [[r.get('rank'), r.get('name'), r.get('solveTime'), r.get('finished')] for r in entries.get('scoreList')]   
    return ranking, entries.get('displayDate'), entries.get('printDate')

def upload_rankings():
    try:
        rankings, date, print_date = get_rankings()
        response = sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        tabs = {tab.get('properties', {}).get('title'):tab.get('properties', {}).get('sheetId') for tab in response.get('sheets')}
        
        tab_id = None
        tab_name = print_date[:print_date.rfind('-')]
        
        for t in tabs:
            if tab_name == t:
                tab_id = tabs[t]
                break
        else:
            new_tab = sheets.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={"requests": {"addSheet": {"properties": {"title": tab_name, "index": 0}}}},
            ).execute()
            tab_id = new_tab.get('replies', [{}])[0].get('addSheet', {}).get('properties', {}).get('sheetId')

        if not tab_id:
            raise IndexError("No valid sheet could be found!")
        else:
            last_date = sheets.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"{tab_name}!A1",
                majorDimension='ROWS'
            ).execute()

            if not last_date.get('values') or last_date.get('values')[0][0] != date:
                sheets.spreadsheets().batchUpdate(
                    spreadsheetId=SHEET_ID,
                    body={"requests": {
                        "insertDimension": {
                            "range": {
                                "sheetId": tab_id,
                                "dimension": "COLUMNS",
                                "startIndex": 0,
                                "endIndex": 4
                            },
                        }
                    }}
                ).execute()
    
            sheets.spreadsheets().values().update(
                spreadsheetId=SHEET_ID, 
                range=f"{tab_name}!A1:D{len(rankings) + 2}",
                valueInputOption="RAW",
                body={
                    "values": [[date, 'Name', 'Time', 'Finished?']] + rankings,
                    "majorDimension": 'ROWS'
                }
            ).execute()
    except IndexError as e:
        print(e)
        print(f"Somefin went wrong - {datetime.datetime.now()}")

if __name__ == "__main__":
    upload_rankings()
    