import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def authenticate():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    token_path = os.path.join(os.path.dirname(__file__), "credentials", "sheets.pickle")
    oauth_path = os.path.join(os.path.dirname(__file__), "credentials", "sheets.json")
    
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token: creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else: 
            flow = InstalledAppFlow.from_client_secrets_file(oauth_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds
    
sheets = build('sheets', 'v4', credentials=authenticate())

if __name__ == "__main__":
    pass
    