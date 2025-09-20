"""Google Drive integration for uploading PDFs and attachments."""

import os
import pickle
from typing import Dict, List, Optional, Any
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from .config import GoogleDriveConfig


class GoogleDriveManager:
    """Manages Google Drive operations for organizing exported emails."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, drive_config: GoogleDriveConfig):
        self.drive_config = drive_config
        self.service = None
        self.credentials = None
        self.root_folder_id = None
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API."""
        try:
            self.credentials = self._get_credentials()
            self.service = build('drive', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Google Drive authentication failed: {e}")
            return False
    
    def _get_credentials(self) -> Credentials:
        """Get or refresh credentials."""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.drive_config.token_file):
            with open(self.drive_config.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.drive_config.credentials_file):
                    raise FileNotFoundError(
                        f"Drive credentials file not found: {self.drive_config.credentials_file}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.drive_config.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.drive_config.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def get_service(self):
        """Get the Google Drive service object."""
        if not self.service:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Google Drive")
        return self.service
    
    def test_connection(self) -> bool:
        """Test the Google Drive API connection."""
        try:
            service = self.get_service()
            about = service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            print(f"Successfully connected to Google Drive for {user_email}")
            return True
        except HttpError as e:
            print(f"Google Drive connection test failed: {e}")
            return False
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a folder in Google Drive."""
        try:
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            print(f"Created folder '{name}' with ID: {folder_id}")
            return folder_id
            
        except HttpError as e:
            print(f"Error creating folder '{name}': {e}")
            return None
    
    def find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Find a folder by name."""
        try:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            return None
            
        except HttpError as e:
            print(f"Error finding folder '{name}': {e}")
            return None
    
    def get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Get existing folder or create new one."""
        folder_id = self.find_folder(name, parent_id)
        
        if folder_id:
            print(f"Found existing folder '{name}': {folder_id}")
            return folder_id
        else:
            return self.create_folder(name, parent_id)
    
    def setup_root_folder(self) -> Optional[str]:
        """Setup the root export folder."""
        if self.root_folder_id:
            return self.root_folder_id
        
        self.root_folder_id = self.get_or_create_folder(self.drive_config.root_folder_name)
        return self.root_folder_id
    
    def setup_domain_folder(self, domain: str) -> Optional[str]:
        """Setup folder for a specific domain."""
        root_id = self.setup_root_folder()
        if not root_id:
            return None
        
        # Sanitize domain name for folder
        folder_name = domain.replace('.', '_')
        return self.get_or_create_folder(folder_name, root_id)
    
    def upload_file(self, file_data: bytes, filename: str, folder_id: str, 
                   mime_type: str = 'application/pdf') -> Optional[str]:
        """Upload a file to Google Drive."""
        try:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(
                BytesIO(file_data),
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            print(f"Uploaded file '{filename}' with ID: {file_id}")
            return file_id
            
        except HttpError as e:
            print(f"Error uploading file '{filename}': {e}")
            return None
    
    def upload_pdf(self, pdf_data: bytes, filename: str, domain: str) -> Optional[str]:
        """Upload a PDF file to the appropriate domain folder."""
        folder_id = self.setup_domain_folder(domain)
        if not folder_id:
            print(f"Failed to setup folder for domain: {domain}")
            return None
        
        return self.upload_file(pdf_data, filename, folder_id, 'application/pdf')
    
    def upload_attachment(self, attachment_data: bytes, filename: str, domain: str, 
                         mime_type: str = 'application/octet-stream') -> Optional[str]:
        """Upload an attachment to the appropriate domain folder."""
        # Create attachments subfolder
        domain_folder_id = self.setup_domain_folder(domain)
        if not domain_folder_id:
            print(f"Failed to setup folder for domain: {domain}")
            return None
        
        attachments_folder_id = self.get_or_create_folder("Attachments", domain_folder_id)
        if not attachments_folder_id:
            print(f"Failed to setup attachments folder for domain: {domain}")
            return None
        
        return self.upload_file(attachment_data, filename, attachments_folder_id, mime_type)


class DriveUploader:
    """Handles batch uploading of PDFs and attachments to Google Drive."""
    
    def __init__(self, drive_manager: GoogleDriveManager):
        self.drive_manager = drive_manager
    
    def upload_domain_exports(self, domain_results: Dict[str, Any]) -> Dict[str, Any]:
        """Upload all exports for a domain."""
        domain = domain_results['domain']
        upload_results = {
            'domain': domain,
            'uploaded_pdfs': [],
            'uploaded_attachments': [],
            'upload_errors': []
        }
        
        print(f"Uploading exports for domain: {domain}")
        
        # Upload PDFs
        for pdf_info in domain_results.get('pdfs', []):
            try:
                file_id = self.drive_manager.upload_pdf(
                    pdf_info['content'],
                    pdf_info['filename'],
                    domain
                )
                
                if file_id:
                    upload_results['uploaded_pdfs'].append({
                        'filename': pdf_info['filename'],
                        'file_id': file_id,
                        'thread_id': pdf_info['thread_id'],
                        'email_count': pdf_info['email_count']
                    })
                    print(f"✓ Uploaded PDF: {pdf_info['filename']}")
                else:
                    error_msg = f"Failed to upload PDF: {pdf_info['filename']}"
                    upload_results['upload_errors'].append(error_msg)
                    print(f"✗ {error_msg}")
            
            except Exception as e:
                error_msg = f"Error uploading PDF {pdf_info['filename']}: {e}"
                upload_results['upload_errors'].append(error_msg)
                print(f"✗ {error_msg}")
        
        # Upload attachments
        for attachment_info in domain_results.get('attachments', []):
            try:
                file_id = self.drive_manager.upload_attachment(
                    attachment_info['content'],
                    attachment_info['filename'],
                    domain
                )
                
                if file_id:
                    upload_results['uploaded_attachments'].append({
                        'filename': attachment_info['filename'],
                        'file_id': file_id,
                        'original_filename': attachment_info['original_filename'],
                        'email_id': attachment_info['email_id'],
                        'thread_id': attachment_info['thread_id']
                    })
                    print(f"✓ Uploaded attachment: {attachment_info['filename']}")
                else:
                    error_msg = f"Failed to upload attachment: {attachment_info['filename']}"
                    upload_results['upload_errors'].append(error_msg)
                    print(f"✗ {error_msg}")
            
            except Exception as e:
                error_msg = f"Error uploading attachment {attachment_info['filename']}: {e}"
                upload_results['upload_errors'].append(error_msg)
                print(f"✗ {error_msg}")
        
        return upload_results
    
    def upload_all_exports(self, all_domain_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload exports for all domains."""
        all_results = {
            'total_domains': len(all_domain_results),
            'domain_results': [],
            'summary': {
                'total_pdfs': 0,
                'total_attachments': 0,
                'total_errors': 0
            }
        }
        
        for domain_results in all_domain_results:
            upload_result = self.upload_domain_exports(domain_results)
            all_results['domain_results'].append(upload_result)
            
            # Update summary
            all_results['summary']['total_pdfs'] += len(upload_result['uploaded_pdfs'])
            all_results['summary']['total_attachments'] += len(upload_result['uploaded_attachments'])
            all_results['summary']['total_errors'] += len(upload_result['upload_errors'])
        
        return all_results