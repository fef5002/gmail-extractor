"""Command-line interface for Gmail Extractor."""

import click
import os
import sys
from pathlib import Path

from .app import GmailExtractorApp
from .config import ConfigManager


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Gmail Extractor - Extract emails from multiple Gmail accounts and export to Google Drive as PDFs.
    
    This tool extracts emails from multiple Gmail accounts based on domain, sender, and recipient filters,
    converts them to PDFs organized by threads, and uploads them to Google Drive with attachments.
    """
    pass


@cli.command()
@click.option(
    '--config', '-c',
    default='config.json',
    help='Path to configuration file (default: config.json)'
)
def run(config):
    """Run the email extraction process."""
    app = GmailExtractorApp(config)
    
    if app.run():
        click.echo("✓ Email extraction completed successfully!")
        sys.exit(0)
    else:
        click.echo("✗ Email extraction failed!")
        sys.exit(1)


@cli.command()
@click.option(
    '--config', '-c',
    default='config.json',
    help='Path to configuration file (default: config.json)'
)
def validate(config):
    """Validate the setup and configuration."""
    app = GmailExtractorApp(config)
    
    if app.validate_setup():
        click.echo("✓ Setup validation successful!")
        sys.exit(0)
    else:
        click.echo("✗ Setup validation failed!")
        sys.exit(1)


@cli.command()
@click.option(
    '--config', '-c',
    default='config.json',
    help='Path to configuration file (default: config.json)'
)
def init_config(config):
    """Create a sample configuration file."""
    config_manager = ConfigManager(config)
    
    if os.path.exists(config):
        if not click.confirm(f'Configuration file {config} already exists. Overwrite?'):
            click.echo("Configuration file creation cancelled.")
            return
    
    try:
        config_manager.create_sample_config()
        click.echo(f"✓ Sample configuration created at: {config}")
        click.echo("\nNext steps:")
        click.echo("1. Edit the configuration file with your account details")
        click.echo("2. Download Gmail API credentials from Google Cloud Console")
        click.echo("3. Download Google Drive API credentials from Google Cloud Console")
        click.echo("4. Run 'gmail-extractor validate' to test your setup")
        click.echo("5. Run 'gmail-extractor run' to start extraction")
    except Exception as e:
        click.echo(f"✗ Error creating configuration: {e}")
        sys.exit(1)


@cli.command()
def setup_guide():
    """Display setup guide for Gmail and Google Drive APIs."""
    guide = """
Gmail Extractor Setup Guide
==========================

1. Enable APIs in Google Cloud Console:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Enable Gmail API and Google Drive API

2. Create OAuth2 Credentials:
   - Go to Credentials section
   - Create OAuth2 Client ID for Desktop Application
   - Download the JSON file

3. Setup Gmail API:
   - Download credentials file for each Gmail account
   - Name them descriptively (e.g., credentials_account1.json)

4. Setup Google Drive API:
   - Download credentials file for the Google Drive account
   - Name it descriptively (e.g., drive_credentials.json)

5. Create Configuration:
   - Run: gmail-extractor init-config
   - Edit config.json with your account details and filters

6. First Run Authentication:
   - Run: gmail-extractor validate
   - Follow browser prompts to authenticate each account
   - Tokens will be saved for future use

7. Start Extraction:
   - Run: gmail-extractor run
   - Monitor progress and check Google Drive for results

Configuration File Structure:
============================
{
  "accounts": [
    {
      "email": "account1@gmail.com",
      "credentials_file": "credentials_account1.json",
      "token_file": "token_account1.json"
    }
  ],
  "drive": {
    "credentials_file": "drive_credentials.json",
    "token_file": "drive_token.json",
    "root_folder_name": "Gmail Exports"
  },
  "filters": {
    "domains": ["example.com"],
    "senders": ["important@example.com"],
    "recipients": ["me@example.com"],
    "include_attachments": true
  },
  "max_filename_length": 100,
  "date_format": "ISO"
}

File Naming Convention:
======================
PDFs: YYYY-MM-DD_domain-name_SenderInitials_RecipientInitials_subject-keywords.pdf
Attachments: YYYY-MM-DD-original-filename.ext

Google Drive Organization:
=========================
Gmail Exports/
├── domain1_com/
│   ├── email1.pdf
│   ├── email2.pdf
│   └── Attachments/
│       ├── 2024-01-01-document.pdf
│       └── 2024-01-02-spreadsheet.xlsx
└── domain2_com/
    ├── email3.pdf
    └── Attachments/
        └── 2024-01-03-presentation.pptx
"""
    click.echo(guide)


@cli.command()
@click.option(
    '--config', '-c',
    default='config.json',
    help='Path to configuration file (default: config.json)'
)
def check_credentials(config):
    """Check if all required credential files exist."""
    if not os.path.exists(config):
        click.echo(f"✗ Configuration file not found: {config}")
        click.echo("Run 'gmail-extractor init-config' to create one.")
        sys.exit(1)
    
    try:
        config_manager = ConfigManager(config)
        cfg = config_manager.load_config()
        
        missing_files = []
        existing_files = []
        
        # Check Gmail credentials
        for account in cfg.accounts:
            if os.path.exists(account.credentials_file):
                existing_files.append(f"Gmail credentials for {account.email}: {account.credentials_file}")
            else:
                missing_files.append(f"Gmail credentials for {account.email}: {account.credentials_file}")
        
        # Check Drive credentials
        if os.path.exists(cfg.drive.credentials_file):
            existing_files.append(f"Drive credentials: {cfg.drive.credentials_file}")
        else:
            missing_files.append(f"Drive credentials: {cfg.drive.credentials_file}")
        
        # Report results
        if existing_files:
            click.echo("✓ Found credential files:")
            for file in existing_files:
                click.echo(f"  {file}")
        
        if missing_files:
            click.echo("\n✗ Missing credential files:")
            for file in missing_files:
                click.echo(f"  {file}")
            click.echo("\nRun 'gmail-extractor setup-guide' for help obtaining credentials.")
            sys.exit(1)
        else:
            click.echo("\n✓ All credential files found!")
    
    except Exception as e:
        click.echo(f"✗ Error checking credentials: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    '--config', '-c',
    default='config.json',
    help='Path to configuration file (default: config.json)'
)
@click.option(
    '--dry-run', '-d',
    is_flag=True,
    help='Show what would be extracted without actually processing'
)
def preview(config, dry_run):
    """Preview what emails would be extracted based on current filters."""
    app = GmailExtractorApp(config)
    
    try:
        # Load configuration
        if not app.load_config():
            sys.exit(1)
        
        # Setup authentication
        if not app.setup_authentication():
            sys.exit(1)
        
        # Setup processors
        if not app.setup_processors():
            sys.exit(1)
        
        # Extract email metadata only
        click.echo("Previewing emails that match current filters...")
        emails_by_domain = app.extract_emails()
        
        if not emails_by_domain:
            click.echo("No emails found matching the current filters.")
            return
        
        total_emails = sum(len(emails) for emails in emails_by_domain.values())
        click.echo(f"\nFound {total_emails} emails across {len(emails_by_domain)} domains:\n")
        
        for domain, emails in emails_by_domain.items():
            click.echo(f"Domain: {domain} ({len(emails)} emails)")
            
            # Group by thread
            threads = {}
            for email in emails:
                thread_id = email.thread_id
                if thread_id not in threads:
                    threads[thread_id] = []
                threads[thread_id].append(email)
            
            click.echo(f"  - {len(threads)} email threads")
            
            # Show some sample subjects
            sample_subjects = list(set([email.subject[:50] + "..." if len(email.subject) > 50 
                                      else email.subject for email in emails[:5]]))
            
            click.echo("  - Sample subjects:")
            for subject in sample_subjects:
                click.echo(f"    • {subject}")
            
            if len(emails) > 5:
                click.echo(f"    ... and {len(emails) - 5} more")
            
            click.echo()
        
        if dry_run:
            click.echo("This was a dry run. No files were processed or uploaded.")
    
    except Exception as e:
        click.echo(f"✗ Preview failed: {e}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()