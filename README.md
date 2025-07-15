# SkylightSync

Automatically sync photos from an iCloud shared album to an email address with a web interface for monitoring and manual control.

## Features

- **Web Scraping**: Scrapes photos from public iCloud shared albums using Selenium
- **Smart Navigation**: Uses carousel navigation to reliably capture all photos in the album
- **Duplicate Prevention**: Tracks already processed photos to avoid duplicates
- **Email Integration**: Sends new photos via email in configurable batches
- **Web UI**: Monitor sync status and trigger manual syncs via web interface
- **Background Monitoring**: Continuously monitors for new photos at configurable intervals
- **Loop Detection**: Automatically stops when all photos have been processed

## Quick Start

### Option 1: Interactive Setup (Recommended)

Run the interactive setup script to guide you through the setup process:

```bash
python setup.py
```

This will check all prerequisites and help you configure the system.

### Option 2: Quick Start Script

```bash
./terminal-start.sh
```

### Option 3: Manual Setup

1. **Prerequisites**:
   - Chrome browser installed
   - Python 3.8+ installed

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install ChromeDriver**:
   - **Mac**: `brew install chromedriver`
   - **Linux**: Download from https://chromedriver.chromium.org/
   - **Windows**: Download from https://chromedriver.chromium.org/

4. **Configure email settings**:
   - Copy `.env.example` to `.env`
   - Add your email credentials (for Gmail, use an app-specific password)

5. **Run the background monitor**:
```bash
# Run background monitor (default: check every 24 hours)
python skylight_sync.py

# Run once and exit
python skylight_sync.py --once

# Custom interval (in seconds)
python skylight_sync.py --interval 1800  # Check every 30 minutes

# Custom batch size
python skylight_sync.py --batch-size 10  # Send 10 photos per email
```

## Web Interface

The application includes a web interface for monitoring and control:

- **Status Page**: View current sync status and statistics
- **Manual Sync**: Trigger immediate sync operations
- **Photo Gallery**: Browse downloaded photos with thumbnails
- **Access**: Available at `http://localhost:5003` when running

### Web UI Features

- Real-time sync status display
- Manual sync trigger button
- Photo gallery with thumbnails
- Download statistics
- Error reporting

## How It Works

### Photo Discovery Process

1. **Album Navigation**: Opens the iCloud shared album URL
2. **Aggressive Scrolling**: Scrolls through the entire album to load all photos
3. **Carousel Navigation**: Clicks into photos and navigates left/right to capture all images
4. **Loop Detection**: Stops when it encounters the first photo again
5. **Duplicate Prevention**: Tracks processed photos to avoid re-downloading

### Email Integration

- **Batch Processing**: Sends photos in configurable batches (default: 5 per email)
- **Email Tracking**: Marks photos as "emailed" in the database
- **SMTP Configuration**: Uses secure SMTP with credentials from `.env`
- **Error Handling**: Graceful handling of email failures

### Data Management

- **Photo Storage**: Downloads stored in `~/Pictures/Skylight` (configurable)
- **Database**: JSON file tracks processed photos and email status
- **Cleanup**: Automatic cleanup of temporary files

## Configuration

### Environment Variables (.env)

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
TO_EMAIL=recipient@example.com

# iCloud Album URL
ICLOUD_ALBUM_URL=https://www.icloud.com/sharedalbum/#B0xxxxxxxxx

# Optional Settings
BATCH_SIZE=5
SYNC_INTERVAL_MINUTES=1440  # Default: 24 hours (1440 minutes)
                            # Common options: 30 (30 min), 60 (1 hour), 
                            # 180 (3 hours), 360 (6 hours), 720 (12 hours), 1440 (24 hours)
PHOTOS_DIRECTORY=~/Pictures/Skylight
```

### Command Line Options

```bash
python skylight_sync.py [options]

Options:
  --once              Run once and exit
  --interval SECONDS  Check interval in seconds (default: 86400)
  --batch-size N      Photos per email (default: 5)
  --help             Show help message
```

## Email Setup for Gmail

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password at https://myaccount.google.com/apppasswords
3. Use this password in the `.env` file (not your regular password)

## File Structure

```
SkylightSync/
├── setup.py              # Interactive setup script
├── terminal-start.sh     # Terminal quick start script
├── skylight_sync.py      # Main sync script
├── icloud_scraper.py     # iCloud scraping logic
├── email_sender.py       # Email integration
├── webui.py             # Web interface
├── requirements.txt      # Python dependencies
├── .env.example        # Environment template
├── README.md           # This file
├── .env                # Configuration (not tracked by git)
├── data/
│   └── processed_photos.json  # Photo tracking database
└── downloads/          # Temporary photo storage
```

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**: Ensure ChromeDriver version matches your Chrome browser version
2. **Email Authentication**: Use app-specific passwords for Gmail, not regular passwords
3. **Permission Errors**: Ensure write permissions for the downloads directory
4. **Network Issues**: Check internet connection and iCloud album accessibility

### Performance Tips

- Run locally with visible browser for best JavaScript handling
- Use appropriate batch sizes to balance email load and processing speed
- Monitor logs for any errors or stuck processes

### Setup Scripts

- **`setup.py`**: Interactive setup with prerequisite checking
- **`terminal-start.sh`**: Quick terminal setup with virtual environment
- **`docker-start.sh`**: Quick Docker setup with build and run

## Development Notes

- The scraper uses Selenium WebDriver with Chrome for reliable JavaScript execution
- Photos are filtered to exclude videos (by content-type and URL extension)
- The system processes approximately 4 photos per second in optimal conditions
- Loop detection prevents infinite processing of the same photos
- Email tracking prevents duplicate sends

## License

This project is open source and available under the MIT License.