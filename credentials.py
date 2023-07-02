# References:
    # https://developers.google.com/drive/api/quickstart/python

# `pip install google-auth-oauthlib`

import json
import os.path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def load_credentials():
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    creds = None

    credentials_json_path = "credentials.json"
    pickle_path = "token.pickle"

    if os.path.exists(pickle_path):
        with open(pickle_path, mode="rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json_path, SCOPES
            )
            creds = flow.run_local_server()
        with open(pickle_path, mode="wb") as token:
            pickle.dump(creds, token)
    return creds

load_credentials()
