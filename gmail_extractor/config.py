"""Configuration management for Gmail Extractor."""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class FilterConfig:
    """Email filtering configuration."""
    domains: List[str]
    senders: List[str]
    recipients: List[str]
    include_attachments: bool = True


@dataclass
class AccountConfig:
    """Gmail account configuration."""
    email: str
    credentials_file: str
    token_file: str


@dataclass
class GoogleDriveConfig:
    """Google Drive configuration."""
    credentials_file: str
    token_file: str
    root_folder_name: str = "Gmail Exports"


@dataclass
class Config:
    """Main configuration for Gmail Extractor."""
    accounts: List[AccountConfig]
    drive: GoogleDriveConfig
    filters: FilterConfig
    max_filename_length: int = 100
    date_format: str = "ISO"


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        # Convert dict data to Config objects
        accounts = [AccountConfig(**acc) for acc in data['accounts']]
        drive = GoogleDriveConfig(**data['drive'])
        filters = FilterConfig(**data['filters'])
        
        self.config = Config(
            accounts=accounts,
            drive=drive,
            filters=filters,
            max_filename_length=data.get('max_filename_length', 100),
            date_format=data.get('date_format', 'ISO')
        )
        
        return self.config
    
    def save_config(self, config: Config) -> None:
        """Save configuration to file."""
        data = {
            'accounts': [asdict(acc) for acc in config.accounts],
            'drive': asdict(config.drive),
            'filters': asdict(config.filters),
            'max_filename_length': config.max_filename_length,
            'date_format': config.date_format
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_sample_config(self) -> None:
        """Create a sample configuration file."""
        sample_config = Config(
            accounts=[
                AccountConfig(
                    email="account1@gmail.com",
                    credentials_file="credentials_account1.json",
                    token_file="token_account1.json"
                ),
                AccountConfig(
                    email="account2@gmail.com",
                    credentials_file="credentials_account2.json",
                    token_file="token_account2.json"
                )
            ],
            drive=GoogleDriveConfig(
                credentials_file="drive_credentials.json",
                token_file="drive_token.json",
                root_folder_name="Gmail Exports"
            ),
            filters=FilterConfig(
                domains=["example.com", "company.com"],
                senders=["important@example.com"],
                recipients=["me@example.com"],
                include_attachments=True
            ),
            max_filename_length=100,
            date_format="ISO"
        )
        
        self.save_config(sample_config)
        print(f"Sample configuration created at: {self.config_path}")