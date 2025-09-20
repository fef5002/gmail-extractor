"""Gmail API authentication and service management."""

import os
import pickle
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import AccountConfig


class GmailAuthenticator:
    """Handles Gmail API authentication for multiple accounts."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, account_config: AccountConfig):
        self.account_config = account_config
        self.service = None
        self.credentials = None
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        try:
            self.credentials = self._get_credentials()
            self.service = build('gmail', 'v1', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Authentication failed for {self.account_config.email}: {e}")
            return False
    
    def _get_credentials(self) -> Credentials:
        """Get or refresh credentials."""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.account_config.token_file):
            with open(self.account_config.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.account_config.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.account_config.credentials_file}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.account_config.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.account_config.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def get_service(self):
        """Get the Gmail service object."""
        if not self.service:
            if not self.authenticate():
                raise Exception(f"Failed to authenticate {self.account_config.email}")
        return self.service
    
    def test_connection(self) -> bool:
        """Test the Gmail API connection."""
        try:
            service = self.get_service()
            profile = service.users().getProfile(userId='me').execute()
            print(f"Successfully connected to {profile.get('emailAddress')}")
            return True
        except HttpError as e:
            print(f"Connection test failed for {self.account_config.email}: {e}")
            return False


class MultiAccountGmailManager:
    """Manages multiple Gmail accounts."""
    
    def __init__(self, account_configs: List[AccountConfig]):
        self.account_configs = account_configs
        self.authenticators = {}
        self.services = {}
    
    def authenticate_all(self) -> bool:
        """Authenticate all accounts."""
        success = True
        
        for config in self.account_configs:
            authenticator = GmailAuthenticator(config)
            if authenticator.authenticate():
                self.authenticators[config.email] = authenticator
                self.services[config.email] = authenticator.get_service()
                print(f"✓ Authenticated {config.email}")
            else:
                print(f"✗ Failed to authenticate {config.email}")
                success = False
        
        return success
    
    def get_service(self, email: str):
        """Get Gmail service for a specific account."""
        return self.services.get(email)
    
    def get_all_services(self) -> dict:
        """Get all authenticated Gmail services."""
        return self.services.copy()
    
    def test_all_connections(self) -> bool:
        """Test connections for all accounts."""
        success = True
        
        for email, authenticator in self.authenticators.items():
            if not authenticator.test_connection():
                success = False
        
        return success