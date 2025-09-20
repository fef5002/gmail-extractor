#!/usr/bin/env python3
"""
Simple test script to verify PDF generation functionality.
This creates a mock email and generates a PDF to test the core functionality.
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the package to the path
sys.path.insert(0, '/home/runner/work/gmail-extractor/gmail-extractor')

from gmail_extractor.pdf_generator import EmailPDFGenerator
from gmail_extractor.extractor import EmailMessage


def create_mock_email_data():
    """Create mock email data for testing."""
    return {
        'id': 'test123',
        'threadId': 'thread123',
        'labelIds': ['INBOX'],
        'snippet': 'This is a test email for PDF generation.',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Email Subject'},
                {'name': 'From', 'value': 'John Doe <john.doe@example.com>'},
                {'name': 'To', 'value': 'Jane Smith <jane.smith@company.com>'},
                {'name': 'Date', 'value': 'Fri, 20 Sep 2024 10:30:00 +0000'},
            ],
            'body': {
                'data': 'VGhpcyBpcyBhIHRlc3QgZW1haWwgYm9keSBjb250ZW50LiBJdCBpbmNsdWRlcyBzb21lIHNhbXBsZSB0ZXh0IHRvIGRlbW9uc3RyYXRlIHRoZSBQREYgZ2VuZXJhdGlvbiBmdW5jdGlvbmFsaXR5Lg=='
                # This is base64 encoded: "This is a test email body content. It includes some sample text to demonstrate the PDF generation functionality."
            },
            'mimeType': 'text/plain'
        }
    }


def test_pdf_generation():
    """Test PDF generation functionality."""
    print("Testing PDF generation functionality...")
    
    try:
        # Create a mock email
        mock_data = create_mock_email_data()
        email = EmailMessage(mock_data, 'test@example.com')
        
        print(f"✓ Created mock email: {email.subject}")
        print(f"  From: {email.sender}")
        print(f"  To: {email.recipient}")
        print(f"  Domain: {email.domain}")
        print(f"  Sender initials: {email.get_sender_initials()}")
        print(f"  Recipient initials: {email.get_recipient_initials()}")
        print(f"  Subject keywords: {email.get_subject_keywords()}")
        
        # Create PDF generator
        pdf_gen = EmailPDFGenerator()
        
        # Generate filename
        filename = pdf_gen.generate_filename([email], email.domain)
        print(f"  Generated filename: {filename}")
        
        # Generate PDF
        pdf_bytes = pdf_gen.generate_thread_pdf([email], email.domain)
        
        print(f"✓ Generated PDF: {len(pdf_bytes)} bytes")
        
        # Save to temporary file for verification
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name
        
        print(f"✓ Saved test PDF to: {temp_path}")
        print(f"  File size: {os.path.getsize(temp_path)} bytes")
        
        # Clean up
        os.unlink(temp_path)
        print("✓ Test PDF cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ PDF generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filename_generation():
    """Test various filename generation scenarios."""
    print("\nTesting filename generation...")
    
    try:
        pdf_gen = EmailPDFGenerator()
        
        # Test cases
        test_cases = [
            {
                'subject': 'Meeting Agenda for Q4 Planning',
                'sender': 'John Doe <john.doe@example.com>',
                'recipient': 'Jane Smith <jane.smith@company.com>',
                'domain': 'example.com'
            },
            {
                'subject': 'Re: Invoice #12345 Payment Confirmation',
                'sender': 'Accounts Payable <ap@vendor.co.uk>',
                'recipient': 'finance@mycompany.org',
                'domain': 'vendor.co.uk'
            },
            {
                'subject': 'Fwd: Project Update - Implementation Phase',
                'sender': '"Project Manager" <pm@consulting-firm.net>',
                'recipient': 'team-leads@mycompany.org',
                'domain': 'consulting-firm.net'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            # Create mock email data
            mock_data = {
                'id': f'test{i}',
                'threadId': f'thread{i}',
                'labelIds': ['INBOX'],
                'snippet': 'Test email snippet',
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': case['subject']},
                        {'name': 'From', 'value': case['sender']},
                        {'name': 'To', 'value': case['recipient']},
                        {'name': 'Date', 'value': 'Fri, 20 Sep 2024 10:30:00 +0000'},
                    ],
                    'body': {'data': 'VGVzdCBjb250ZW50'},
                    'mimeType': 'text/plain'
                }
            }
            
            email = EmailMessage(mock_data, 'test@example.com')
            filename = pdf_gen.generate_filename([email], case['domain'])
            
            print(f"  Test {i}:")
            print(f"    Subject: {case['subject']}")
            print(f"    Sender: {case['sender']}")
            print(f"    Generated: {filename}")
            print(f"    Length: {len(filename)} characters")
        
        print("✓ Filename generation tests completed")
        return True
        
    except Exception as e:
        print(f"✗ Filename generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Gmail Extractor - Basic Functionality Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_pdf_generation()
    success &= test_filename_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)