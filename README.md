# Gmail Extractor

A comprehensive tool that extracts emails from multiple Gmail accounts based on domain, sender, and recipient filters, converts them to PDFs organized by email threads, and uploads them to Google Drive with attachments properly organized.

## Features

- **Multi-Account Support**: Extract emails from multiple Gmail accounts simultaneously
- **Advanced Filtering**: Filter emails by domains, specific senders, and recipients
- **Thread Organization**: Groups related emails into threads and exports as single PDFs
- **Attachment Handling**: Extracts and organizes email attachments with date-prepended filenames
- **Google Drive Integration**: Automatically uploads PDFs and attachments to organized folders
- **Smart Naming**: Generates filenames with ISO dates, domain names, sender/recipient initials, and subject keywords
- **Comprehensive CLI**: Easy-to-use command-line interface with setup guidance

## Installation

1. Clone the repository:
```bash
git clone https://github.com/fef5002/gmail-extractor.git
cd gmail-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

## Quick Start

1. **Initialize configuration**:
```bash
gmail-extractor init-config
```

2. **Setup Google APIs** (see detailed setup guide below):
   - Enable Gmail API and Google Drive API in Google Cloud Console
   - Download OAuth2 credentials for each account
   - Place credential files in the project directory

3. **Edit configuration**:
   Edit `config.json` with your account details and filtering preferences

4. **Validate setup**:
```bash
gmail-extractor validate
```

5. **Run extraction**:
```bash
gmail-extractor run
```

## Configuration

The tool uses a JSON configuration file (`config.json`) with the following structure:

```json
{
  "accounts": [
    {
      "email": "account1@gmail.com",
      "credentials_file": "credentials_account1.json",
      "token_file": "token_account1.json"
    },
    {
      "email": "account2@gmail.com",
      "credentials_file": "credentials_account2.json",
      "token_file": "token_account2.json"
    }
  ],
  "drive": {
    "credentials_file": "drive_credentials.json",
    "token_file": "drive_token.json",
    "root_folder_name": "Gmail Exports"
  },
  "filters": {
    "domains": ["example.com", "company.com"],
    "senders": ["important@example.com"],
    "recipients": ["me@example.com"],
    "include_attachments": true
  },
  "max_filename_length": 100,
  "date_format": "ISO"
}
```

### Configuration Options

- **accounts**: List of Gmail accounts to extract from
- **drive**: Google Drive configuration for upload destination
- **filters**: Email filtering criteria
- **max_filename_length**: Maximum length for generated filenames
- **date_format**: Date format for filenames (ISO recommended)

## Google API Setup

### 1. Enable APIs
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API and Google Drive API

### 2. Create OAuth2 Credentials
1. Go to the Credentials section
2. Create OAuth2 Client ID for Desktop Application
3. Download the JSON credential file

### 3. Setup Files
- Place Gmail API credentials for each account in your project directory
- Place Google Drive API credentials in your project directory
- Update the configuration file with the correct file paths

## Usage

### Command Line Interface

```bash
# Initialize configuration
gmail-extractor init-config

# Validate setup and test authentication
gmail-extractor validate

# Check if all credential files exist
gmail-extractor check-credentials

# Preview what would be extracted (without processing)
gmail-extractor preview --dry-run

# Run the full extraction process
gmail-extractor run

# Show detailed setup guide
gmail-extractor setup-guide
```

### File Organization

The tool organizes exported files in Google Drive as follows:

```
Gmail Exports/
├── domain1_com/
│   ├── 2024-01-15_domain1-com_JS_MR_meeting-agenda.pdf
│   ├── 2024-01-16_domain1-com_AB_CD_project-update.pdf
│   └── Attachments/
│       ├── 2024-01-15-meeting-agenda.pdf
│       └── 2024-01-16-project-proposal.docx
└── domain2_com/
    ├── 2024-01-17_domain2-com_XY_PQ_invoice-payment.pdf
    └── Attachments/
        └── 2024-01-17-invoice.pdf
```

### Filename Convention

**PDFs**: `YYYY-MM-DD_domain-name_SenderInitials_RecipientInitials_subject-keywords.pdf`

**Attachments**: `YYYY-MM-DD-original-filename.ext`

- Date is in ISO format (YYYY-MM-DD)
- Domain names have dots replaced with hyphens
- Initials are extracted from sender/recipient names (max 3 characters)
- Subject keywords are the first 3 meaningful words from the subject line
- Hyphens are used as separators throughout

## Features in Detail

### Multi-Account Email Extraction
- Supports multiple Gmail accounts simultaneously
- Independent authentication for each account
- Consolidated results organized by domain

### Advanced Email Filtering
- **Domain filtering**: Extract emails from/to specific domains
- **Sender filtering**: Target emails from specific senders
- **Recipient filtering**: Target emails to specific recipients
- **Combination filtering**: All filters work together with AND logic

### Thread-Based PDF Generation
- Groups related emails into conversation threads
- Generates one PDF per thread containing all emails
- Maintains chronological order within threads
- Includes email metadata (from, to, date, subject)
- Converts HTML content to readable text

### Attachment Management
- Extracts all email attachments
- Prepends ISO date to attachment filenames
- Maintains original file extensions
- Organizes attachments in separate folders per domain
- Handles filename conflicts automatically

### Google Drive Integration
- Creates organized folder structure automatically
- Separates PDFs and attachments
- Handles authentication and token refresh
- Provides upload progress and error reporting

## Error Handling

The tool includes comprehensive error handling:
- Authentication failures are clearly reported
- Network issues are handled gracefully
- File conflicts are resolved automatically
- Detailed error messages help with troubleshooting

## Requirements

- Python 3.8+
- Google account with Gmail and Drive access
- Google Cloud Project with enabled APIs
- Valid OAuth2 credentials

## Dependencies

See `requirements.txt` for the complete list of dependencies:
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- reportlab
- python-dateutil
- click
- beautifulsoup4
- lxml

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure credential files are valid and in the correct location
2. **API Quota Exceeded**: Check Google Cloud Console for API usage limits
3. **Permission Denied**: Verify OAuth2 scopes include necessary permissions
4. **File Upload Errors**: Check Google Drive storage space and permissions

### Getting Help

1. Run `gmail-extractor setup-guide` for detailed setup instructions
2. Use `gmail-extractor validate` to test your configuration
3. Check the console output for detailed error messages
4. Ensure all credential files are properly configured

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
