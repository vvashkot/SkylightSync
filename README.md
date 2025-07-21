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

### Prerequisites

- **Chrome browser** installed
- **Python 3.8+** installed
- **Virtual environment** (recommended for isolation)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd SkylightSync
```

2. **Create and activate a virtual environment**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install ChromeDriver**:
   - **Mac**: `brew install chromedriver`
   - **Linux**: Download from https://chromedriver.chromium.org/
   - **Windows**: Download from https://chromedriver.chromium.org/

5. **Configure email settings**:
   - Copy `.env.example` to `.env`
   - Edit `.env` with your email credentials (for Gmail, use an app-specific password)

6. **Run the application**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On macOS/Linux

# Run background monitor (default: check every 24 hours)
python skylight_sync.py

# Run once and exit
python skylight_sync.py --once

# Custom interval (in seconds)
python skylight_sync.py --interval 1800  # Check every 30 minutes

# Custom batch size
python skylight_sync.py --batch-size 10  # Send 10 photos per email
```

### Option 1: Interactive Setup (Recommended)

Run the interactive setup script to guide you through the setup process:

```bash
# Activate virtual environment first
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Run setup
python setup.py
```

This will check all prerequisites and help you configure the system, including an option to set up **automated daily sync** using:
- **macOS/Linux**: Cron job (runs at 9:00 AM daily)
- **Windows**: Task Scheduler (runs at 9:00 AM daily)

### Option 2: Quick Start Script

```bash
./terminal-start.sh
```

## Automated Scheduling

The setup script can automatically configure daily sync jobs:

### macOS/Linux (Cron Job)
- Creates a shell script: `run_skylight_sync.sh`
- Adds cron job to run daily at 9:00 AM
- Logs output to: `cron.log`
- View/edit: `crontab -e`
- Remove: `crontab -l | grep -v skylight | crontab -`

### Windows (Task Scheduler)
- Creates a batch script: `run_skylight_sync.bat`
- Adds Windows Task: `SkylightSync_Daily`
- Runs daily at 9:00 AM
- View/edit: Task Scheduler → `SkylightSync_Daily`
- Remove: `schtasks /delete /tn "SkylightSync_Daily"`

### Manual Cron Setup (Advanced)

If you prefer to set up the cron job manually:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * /path/to/your/SkylightSync/run_skylight_sync.sh >> /path/to/your/SkylightSync/cron.log 2>&1
```

## Virtual Environment Usage

**Important**: Always use a virtual environment to avoid conflicts with system Python packages.

### Creating a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Daily Usage

```bash
# Always activate the virtual environment before running the script
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Then run the application
python skylight_sync.py
```

### Deactivating the Virtual Environment

```bash
deactivate
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