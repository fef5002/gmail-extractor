"""PDF generation functionality for email threads."""

import os
import re
import tempfile
from typing import List, Dict, Any
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import black, blue, gray
from bs4 import BeautifulSoup

from .extractor import EmailMessage


class EmailPDFGenerator:
    """Generates PDF files from email threads."""
    
    def __init__(self, max_filename_length: int = 100):
        self.max_filename_length = max_filename_length
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF generation."""
        # Email header style
        self.styles.add(ParagraphStyle(
            name='EmailHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=blue,
            spaceAfter=6,
            spaceBefore=12
        ))
        
        # Email metadata style
        self.styles.add(ParagraphStyle(
            name='EmailMeta',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=gray,
            spaceAfter=6
        ))
        
        # Email content style
        self.styles.add(ParagraphStyle(
            name='EmailContent',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leftIndent=20
        ))
    
    def generate_filename(self, thread_emails: List[EmailMessage], domain: str) -> str:
        """Generate filename based on the requirements."""
        if not thread_emails:
            return "empty-thread.pdf"
        
        # Use the first email in thread for metadata
        first_email = thread_emails[0]
        
        # ISO date
        date_str = first_email.date.strftime('%Y-%m-%d') if first_email.date else 'unknown-date'
        
        # DNS (domain)
        dns = domain.replace('.', '-')
        
        # Sender initials
        sender_initials = first_email.get_sender_initials()
        
        # Recipient initials
        recipient_initials = first_email.get_recipient_initials()
        
        # Subject keywords
        subject_keywords = first_email.get_subject_keywords()
        
        # Combine all parts
        filename_parts = [
            date_str,
            dns,
            sender_initials,
            recipient_initials,
            subject_keywords
        ]
        
        filename = '_'.join(filename_parts) + '.pdf'
        
        # Sanitize filename
        filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
        filename = re.sub(r'-+', '-', filename)  # Replace multiple hyphens with single
        
        # Truncate if too long
        if len(filename) > self.max_filename_length:
            base_name = filename[:-4]  # Remove .pdf
            truncated = base_name[:self.max_filename_length - 4]
            filename = truncated + '.pdf'
        
        return filename
    
    def generate_thread_pdf(self, thread_emails: List[EmailMessage], domain: str) -> bytes:
        """Generate PDF for an email thread."""
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build content
        story = []
        
        # Add title page
        story.append(Paragraph(f"Email Thread - {domain}", self.styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Paragraph(f"Number of emails: {len(thread_emails)}", self.styles['Normal']))
        story.append(PageBreak())
        
        # Add each email
        for i, email in enumerate(thread_emails):
            story.extend(self._create_email_content(email, i + 1))
            if i < len(thread_emails) - 1:  # Add page break between emails (except last)
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_email_content(self, email: EmailMessage, email_number: int) -> List[Any]:
        """Create content for a single email."""
        content = []
        
        # Email header
        content.append(Paragraph(f"Email #{email_number}", self.styles['EmailHeader']))
        
        # Email metadata
        meta_lines = [
            f"<b>From:</b> {self._escape_html(email.sender)}",
            f"<b>To:</b> {self._escape_html(email.recipient)}",
            f"<b>Subject:</b> {self._escape_html(email.subject)}",
            f"<b>Date:</b> {email.date.strftime('%Y-%m-%d %H:%M:%S %Z') if email.date else 'Unknown'}",
            f"<b>Account:</b> {self._escape_html(email.account_email)}",
        ]
        
        for line in meta_lines:
            content.append(Paragraph(line, self.styles['EmailMeta']))
        
        content.append(Spacer(1, 12))
        
        # Email content
        email_content = self._get_email_body(email)
        if email_content:
            # Split content into paragraphs to avoid reportlab issues with long text
            paragraphs = email_content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    content.append(Paragraph(self._escape_html(paragraph), self.styles['EmailContent']))
        else:
            content.append(Paragraph("<i>No content available</i>", self.styles['EmailContent']))
        
        # Attachments info
        if email.attachments:
            content.append(Spacer(1, 12))
            content.append(Paragraph("<b>Attachments:</b>", self.styles['EmailMeta']))
            for attachment in email.attachments:
                att_info = f"• {attachment['filename']} ({attachment.get('size', 0)} bytes)"
                content.append(Paragraph(self._escape_html(att_info), self.styles['EmailMeta']))
        
        return content
    
    def _get_email_body(self, email: EmailMessage) -> str:
        """Extract readable body from email."""
        if email.html_content:
            # Convert HTML to plain text
            soup = BeautifulSoup(email.html_content, 'html.parser')
            return soup.get_text()
        elif email.text_content:
            return email.text_content
        else:
            return email.snippet or "No content available"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters for reportlab."""
        if not text:
            return ""
        
        # Basic HTML escaping
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text


class AttachmentProcessor:
    """Processes email attachments."""
    
    def __init__(self):
        pass
    
    def generate_attachment_filename(self, email: EmailMessage, attachment: dict) -> str:
        """Generate filename for attachment with date prepended."""
        original_filename = attachment.get('filename', 'unknown_attachment')
        
        # Get date from email
        date_str = email.date.strftime('%Y-%m-%d') if email.date else 'unknown-date'
        
        # Split filename and extension
        name_parts = original_filename.rsplit('.', 1)
        if len(name_parts) == 2:
            name, extension = name_parts
            new_filename = f"{date_str}-{name}.{extension}"
        else:
            new_filename = f"{date_str}-{original_filename}"
        
        # Sanitize filename
        new_filename = re.sub(r'[<>:"/\\|?*]', '-', new_filename)
        new_filename = re.sub(r'-+', '-', new_filename)  # Replace multiple hyphens with single
        
        return new_filename
    
    def save_attachment(self, attachment_data: bytes, filename: str, output_dir: str) -> str:
        """Save attachment to file."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # Handle filename conflicts
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            name_parts = original_filepath.rsplit('.', 1)
            if len(name_parts) == 2:
                name, extension = name_parts
                filepath = f"{name}_{counter}.{extension}"
            else:
                filepath = f"{original_filepath}_{counter}"
            counter += 1
        
        with open(filepath, 'wb') as f:
            f.write(attachment_data)
        
        return filepath


class BatchPDFProcessor:
    """Processes multiple email threads into PDFs."""
    
    def __init__(self, extractors: Dict[str, Any], max_filename_length: int = 100):
        self.extractors = extractors
        self.pdf_generator = EmailPDFGenerator(max_filename_length)
        self.attachment_processor = AttachmentProcessor()
    
    def process_domain_emails(self, domain: str, emails: List[EmailMessage], 
                            include_attachments: bool = True) -> Dict[str, Any]:
        """Process all emails for a domain into PDFs."""
        results = {
            'domain': domain,
            'pdfs': [],
            'attachments': [],
            'errors': []
        }
        
        # Group emails by thread
        threads = {}
        for email in emails:
            thread_id = email.thread_id
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(email)
        
        # Sort emails within each thread by date
        for thread_id in threads:
            threads[thread_id].sort(key=lambda x: x.date or datetime.min)
        
        # Process each thread
        for thread_id, thread_emails in threads.items():
            try:
                # Generate PDF
                pdf_bytes = self.pdf_generator.generate_thread_pdf(thread_emails, domain)
                filename = self.pdf_generator.generate_filename(thread_emails, domain)
                
                results['pdfs'].append({
                    'filename': filename,
                    'content': pdf_bytes,
                    'thread_id': thread_id,
                    'email_count': len(thread_emails)
                })
                
                # Process attachments if requested
                if include_attachments:
                    for email in thread_emails:
                        for attachment in email.attachments:
                            try:
                                # Get the extractor for this email's account
                                extractor = self.extractors.get(email.account_email)
                                if extractor and attachment.get('attachment_id'):
                                    attachment_data = extractor.download_attachment(
                                        email.message_id, 
                                        attachment['attachment_id']
                                    )
                                    
                                    if attachment_data:
                                        att_filename = self.attachment_processor.generate_attachment_filename(
                                            email, attachment
                                        )
                                        
                                        results['attachments'].append({
                                            'filename': att_filename,
                                            'content': attachment_data,
                                            'original_filename': attachment['filename'],
                                            'email_id': email.message_id,
                                            'thread_id': thread_id
                                        })
                            
                            except Exception as e:
                                error_msg = f"Failed to download attachment {attachment.get('filename', 'unknown')} from email {email.message_id}: {e}"
                                results['errors'].append(error_msg)
                                print(error_msg)
            
            except Exception as e:
                error_msg = f"Failed to process thread {thread_id}: {e}"
                results['errors'].append(error_msg)
                print(error_msg)
        
        return results