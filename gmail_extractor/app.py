"""Main Gmail Extractor application orchestration."""

import os
import sys
from typing import Dict, List, Any
from datetime import datetime

from .config import ConfigManager, Config
from .auth import MultiAccountGmailManager
from .extractor import EmailProcessor
from .pdf_generator import BatchPDFProcessor
from .drive_manager import GoogleDriveManager, DriveUploader


class GmailExtractorApp:
    """Main application class that orchestrates the email extraction process."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_manager = ConfigManager(config_path)
        self.config: Config = None
        self.gmail_manager: MultiAccountGmailManager = None
        self.drive_manager: GoogleDriveManager = None
        self.email_processor: EmailProcessor = None
        self.pdf_processor: BatchPDFProcessor = None
        self.drive_uploader: DriveUploader = None
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            self.config = self.config_manager.load_config()
            print(f"✓ Loaded configuration with {len(self.config.accounts)} accounts")
            return True
        except FileNotFoundError:
            print(f"✗ Configuration file not found. Creating sample config...")
            self.config_manager.create_sample_config()
            print(f"Please edit the configuration file and run again.")
            return False
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            return False
    
    def setup_authentication(self) -> bool:
        """Setup authentication for Gmail and Google Drive."""
        if not self.config:
            print("✗ Configuration not loaded")
            return False
        
        # Setup Gmail authentication
        print("Setting up Gmail authentication...")
        self.gmail_manager = MultiAccountGmailManager(self.config.accounts)
        
        if not self.gmail_manager.authenticate_all():
            print("✗ Failed to authenticate all Gmail accounts")
            return False
        
        # Test Gmail connections
        if not self.gmail_manager.test_all_connections():
            print("✗ Gmail connection tests failed")
            return False
        
        # Setup Google Drive authentication
        print("Setting up Google Drive authentication...")
        self.drive_manager = GoogleDriveManager(self.config.drive)
        
        if not self.drive_manager.authenticate():
            print("✗ Failed to authenticate with Google Drive")
            return False
        
        # Test Drive connection
        if not self.drive_manager.test_connection():
            print("✗ Google Drive connection test failed")
            return False
        
        print("✓ All authentication successful")
        return True
    
    def setup_processors(self) -> bool:
        """Setup email and PDF processors."""
        if not self.gmail_manager or not self.drive_manager:
            print("✗ Authentication not completed")
            return False
        
        # Setup email processor
        gmail_services = self.gmail_manager.get_all_services()
        self.email_processor = EmailProcessor(gmail_services)
        
        # Setup PDF processor
        extractors = {
            email: self.gmail_manager.get_service(email)
            for email in gmail_services.keys()
        }
        self.pdf_processor = BatchPDFProcessor(
            {email: extractor for email, extractor in self.email_processor.extractors.items()},
            self.config.max_filename_length
        )
        
        # Setup Drive uploader
        self.drive_uploader = DriveUploader(self.drive_manager)
        
        print("✓ Processors setup complete")
        return True
    
    def extract_emails(self) -> Dict[str, List[Any]]:
        """Extract emails from all accounts based on filters."""
        if not self.email_processor:
            raise Exception("Email processor not setup")
        
        print("Extracting emails from all accounts...")
        emails_by_domain = self.email_processor.extract_all_emails(self.config.filters)
        
        total_emails = sum(len(emails) for emails in emails_by_domain.values())
        print(f"✓ Extracted {total_emails} emails across {len(emails_by_domain)} domains")
        
        for domain, emails in emails_by_domain.items():
            print(f"  - {domain}: {len(emails)} emails")
        
        return emails_by_domain
    
    def process_emails_to_pdfs(self, emails_by_domain: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Process emails into PDFs and organize attachments."""
        if not self.pdf_processor:
            raise Exception("PDF processor not setup")
        
        print("Processing emails into PDFs...")
        all_domain_results = []
        
        for domain, emails in emails_by_domain.items():
            print(f"Processing domain: {domain}")
            
            domain_results = self.pdf_processor.process_domain_emails(
                domain, 
                emails, 
                self.config.filters.include_attachments
            )
            
            all_domain_results.append(domain_results)
            
            print(f"  - Generated {len(domain_results['pdfs'])} PDFs")
            print(f"  - Extracted {len(domain_results['attachments'])} attachments")
            
            if domain_results['errors']:
                print(f"  - {len(domain_results['errors'])} errors occurred")
        
        return all_domain_results
    
    def upload_to_drive(self, all_domain_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload PDFs and attachments to Google Drive."""
        if not self.drive_uploader:
            raise Exception("Drive uploader not setup")
        
        print("Uploading files to Google Drive...")
        upload_results = self.drive_uploader.upload_all_exports(all_domain_results)
        
        summary = upload_results['summary']
        print(f"✓ Upload complete:")
        print(f"  - {summary['total_pdfs']} PDFs uploaded")
        print(f"  - {summary['total_attachments']} attachments uploaded")
        
        if summary['total_errors'] > 0:
            print(f"  - {summary['total_errors']} errors occurred")
        
        return upload_results
    
    def run(self) -> bool:
        """Run the complete email extraction process."""
        print("=" * 60)
        print("Gmail Extractor - Starting extraction process")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Load configuration
            if not self.load_config():
                return False
            
            # Setup authentication
            if not self.setup_authentication():
                return False
            
            # Setup processors
            if not self.setup_processors():
                return False
            
            # Extract emails
            emails_by_domain = self.extract_emails()
            
            if not emails_by_domain:
                print("No emails found matching the filters")
                return True
            
            # Process emails to PDFs
            all_domain_results = self.process_emails_to_pdfs(emails_by_domain)
            
            # Upload to Google Drive
            upload_results = self.upload_to_drive(all_domain_results)
            
            # Final summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("=" * 60)
            print("Extraction completed successfully!")
            print(f"Duration: {duration}")
            print(f"Processed {len(emails_by_domain)} domains")
            print(f"Generated {upload_results['summary']['total_pdfs']} PDFs")
            print(f"Extracted {upload_results['summary']['total_attachments']} attachments")
            print("=" * 60)
            
            return True
        
        except KeyboardInterrupt:
            print("\n✗ Process interrupted by user")
            return False
        
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def validate_setup(self) -> bool:
        """Validate the setup without running extraction."""
        print("Validating Gmail Extractor setup...")
        
        try:
            # Load configuration
            if not self.load_config():
                return False
            
            # Check if credential files exist
            missing_files = []
            
            for account in self.config.accounts:
                if not os.path.exists(account.credentials_file):
                    missing_files.append(f"Gmail credentials: {account.credentials_file}")
            
            if not os.path.exists(self.config.drive.credentials_file):
                missing_files.append(f"Drive credentials: {self.config.drive.credentials_file}")
            
            if missing_files:
                print("✗ Missing credential files:")
                for file in missing_files:
                    print(f"  - {file}")
                return False
            
            # Test authentication
            if not self.setup_authentication():
                return False
            
            print("✓ Setup validation successful!")
            return True
        
        except Exception as e:
            print(f"✗ Setup validation failed: {e}")
            return False