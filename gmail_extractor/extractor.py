"""Email extraction and filtering functionality."""

import base64
import email
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError

from .config import FilterConfig


class EmailMessage:
    """Represents an email message with metadata and content."""
    
    def __init__(self, message_data: dict, account_email: str):
        self.account_email = account_email
        self.message_id = message_data.get('id')
        self.thread_id = message_data.get('threadId')
        self.labels = message_data.get('labelIds', [])
        self.snippet = message_data.get('snippet', '')
        
        # Parse headers
        self.headers = {}
        self.subject = ""
        self.sender = ""
        self.recipient = ""
        self.date = None
        self.domain = ""
        
        if 'payload' in message_data:
            self._parse_headers(message_data['payload'].get('headers', []))
        
        # Content
        self.html_content = ""
        self.text_content = ""
        self.attachments = []
        
        if 'payload' in message_data:
            self._parse_content(message_data['payload'])
    
    def _parse_headers(self, headers: List[dict]):
        """Parse email headers."""
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            self.headers[name] = value
            
            if name == 'subject':
                self.subject = value
            elif name == 'from':
                self.sender = value
                # Extract domain from sender
                email_match = re.search(r'@([^>\s]+)', value)
                if email_match:
                    self.domain = email_match.group(1)
            elif name == 'to':
                self.recipient = value
            elif name == 'date':
                try:
                    self.date = datetime.strptime(value, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    try:
                        # Alternative date format
                        self.date = datetime.strptime(value.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')
                    except ValueError:
                        print(f"Could not parse date: {value}")
                        self.date = datetime.now()
    
    def _parse_content(self, payload: dict):
        """Parse email content and attachments."""
        if payload.get('parts'):
            for part in payload['parts']:
                self._parse_part(part)
        else:
            self._parse_part(payload)
    
    def _parse_part(self, part: dict):
        """Parse a single part of the email."""
        mime_type = part.get('mimeType', '')
        filename = part.get('filename', '')
        
        if filename:  # This is an attachment
            attachment_data = {
                'filename': filename,
                'mime_type': mime_type,
                'size': part.get('body', {}).get('size', 0),
                'attachment_id': part.get('body', {}).get('attachmentId')
            }
            self.attachments.append(attachment_data)
        elif mime_type == 'text/html':
            data = part.get('body', {}).get('data')
            if data:
                self.html_content += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif mime_type == 'text/plain':
            data = part.get('body', {}).get('data')
            if data:
                self.text_content += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif part.get('parts'):
            for subpart in part['parts']:
                self._parse_part(subpart)
    
    def get_sender_initials(self) -> str:
        """Extract initials from sender name."""
        # Extract name from email format "Name <email@domain.com>"
        name_match = re.search(r'^([^<]+)', self.sender)
        if name_match:
            name = name_match.group(1).strip().strip('"')
        else:
            # If no name, use email local part
            email_match = re.search(r'([^@]+)@', self.sender)
            name = email_match.group(1) if email_match else self.sender
        
        # Extract initials
        words = re.findall(r'\b\w+', name)
        initials = ''.join([word[0].upper() for word in words[:3]])  # Max 3 initials
        return initials if initials else 'UNK'
    
    def get_recipient_initials(self) -> str:
        """Extract initials from recipient name."""
        # Similar logic to sender initials
        name_match = re.search(r'^([^<]+)', self.recipient)
        if name_match:
            name = name_match.group(1).strip().strip('"')
        else:
            email_match = re.search(r'([^@]+)@', self.recipient)
            name = email_match.group(1) if email_match else self.recipient
        
        words = re.findall(r'\b\w+', name)
        initials = ''.join([word[0].upper() for word in words[:3]])
        return initials if initials else 'UNK'
    
    def get_subject_keywords(self, max_words: int = 3) -> str:
        """Extract keywords from subject line."""
        # Remove common prefixes and clean the subject
        subject = re.sub(r'^(re|fwd?):\s*', '', self.subject, flags=re.IGNORECASE)
        
        # Extract meaningful words (alphanumeric, length > 2)
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', subject)
        
        # Take first few words and join with hyphens
        keywords = '-'.join(words[:max_words]).lower()
        return keywords if keywords else 'no-subject'


class EmailExtractor:
    """Extracts emails from Gmail accounts based on filters."""
    
    def __init__(self, gmail_service, account_email: str):
        self.service = gmail_service
        self.account_email = account_email
    
    def search_messages(self, filters: FilterConfig, max_results: int = 100) -> List[str]:
        """Search for messages based on filters."""
        query_parts = []
        
        # Add domain filters
        if filters.domains:
            domain_queries = [f"from:@{domain} OR to:@{domain}" for domain in filters.domains]
            query_parts.append(f"({' OR '.join(domain_queries)})")
        
        # Add sender filters
        if filters.senders:
            sender_queries = [f"from:{sender}" for sender in filters.senders]
            query_parts.append(f"({' OR '.join(sender_queries)})")
        
        # Add recipient filters
        if filters.recipients:
            recipient_queries = [f"to:{recipient}" for recipient in filters.recipients]
            query_parts.append(f"({' OR '.join(recipient_queries)})")
        
        # Combine all filters with AND
        query = ' AND '.join(query_parts) if query_parts else ""
        
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            message_ids = [msg['id'] for msg in messages]
            
            print(f"Found {len(message_ids)} messages in {self.account_email}")
            return message_ids
            
        except HttpError as e:
            print(f"Error searching messages in {self.account_email}: {e}")
            return []
    
    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        """Get a specific message by ID."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return EmailMessage(message, self.account_email)
            
        except HttpError as e:
            print(f"Error getting message {message_id}: {e}")
            return None
    
    def get_thread_messages(self, thread_id: str) -> List[EmailMessage]:
        """Get all messages in a thread."""
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            messages = []
            for message_data in thread.get('messages', []):
                email_msg = EmailMessage(message_data, self.account_email)
                messages.append(email_msg)
            
            return messages
            
        except HttpError as e:
            print(f"Error getting thread {thread_id}: {e}")
            return []
    
    def download_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Download an attachment."""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment.get('data')
            if data:
                return base64.urlsafe_b64decode(data)
            
        except HttpError as e:
            print(f"Error downloading attachment {attachment_id}: {e}")
        
        return None


class EmailProcessor:
    """Processes emails and organizes them by domain and threads."""
    
    def __init__(self, gmail_services: Dict[str, Any]):
        self.gmail_services = gmail_services
        self.extractors = {
            email: EmailExtractor(service, email)
            for email, service in gmail_services.items()
        }
    
    def extract_all_emails(self, filters: FilterConfig) -> Dict[str, List[EmailMessage]]:
        """Extract emails from all accounts and organize by domain."""
        emails_by_domain = {}
        
        for account_email, extractor in self.extractors.items():
            print(f"Extracting emails from {account_email}...")
            
            message_ids = extractor.search_messages(filters)
            
            for message_id in message_ids:
                email_msg = extractor.get_message(message_id)
                if email_msg and email_msg.domain:
                    domain = email_msg.domain
                    if domain not in emails_by_domain:
                        emails_by_domain[domain] = []
                    emails_by_domain[domain].append(email_msg)
        
        return emails_by_domain
    
    def group_by_threads(self, emails: List[EmailMessage]) -> Dict[str, List[EmailMessage]]:
        """Group emails by thread ID."""
        threads = {}
        
        for email in emails:
            thread_id = email.thread_id
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(email)
        
        # Sort emails within each thread by date
        for thread_id in threads:
            threads[thread_id].sort(key=lambda x: x.date or datetime.min)
        
        return threads