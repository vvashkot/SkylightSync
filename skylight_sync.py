#!/usr/bin/env python3

import os
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from icloud_scraper import ICloudPhotoScraper
from email_sender import EmailSender
import json

class BackgroundPhotoMonitor:
    def __init__(self):
        self.running = False
        self.sync_thread = None
        self.last_sync = None
        self.sync_interval = int(os.getenv('SYNC_INTERVAL_MINUTES', '1440')) * 60  # Default 24 hours (1440 minutes)
        self.photos_directory = os.path.expanduser(os.getenv('PHOTOS_DIRECTORY', '~/Pictures/Skylight'))
        self.album_url = os.getenv('ICLOUD_ALBUM_URL')
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _format_interval(self, minutes):
        """Format sync interval in a user-friendly way"""
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:
            hours = minutes // 60
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = minutes // 1440
            return f"{days} day{'s' if days != 1 else ''}"
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def update_status(self, last_sync=None, last_error=None, photos_sent=None):
        """Update status file with sync information"""
        status_file = os.path.join('data', 'status.json')
        status = {}
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                try:
                    status = json.load(f)
                except Exception:
                    status = {}
        
        if last_sync is not None:
            status['last_sync'] = last_sync
        if last_error is not None:
            status['last_error'] = last_error
        if photos_sent is not None:
            status['photos_sent'] = photos_sent
        
        # Add background process info
        status['background_active'] = self.running
        status['sync_interval_minutes'] = self.sync_interval // 60
        if self.last_sync:
            status['next_sync'] = (self.last_sync + timedelta(seconds=self.sync_interval)).isoformat()
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def run_sync_once(self):
        """Run a single sync operation with proper locking"""
        if not self.album_url:
            return False, "ICLOUD_ALBUM_URL not configured"
        
        # Create a lock file to prevent conflicts with manual sync
        lock_file = os.path.join('data', 'background_sync.lock')
        manual_lock_file = os.path.join('data', 'scraper.lock')
        
        # Check if manual sync is running
        if os.path.exists(manual_lock_file):
            print("Manual sync is running, skipping background sync")
            return False, "Manual sync in progress"
        
        # Check if another background sync is running
        if os.path.exists(lock_file):
            print("Another background sync is running, skipping")
            return False, "Another background sync is running"
        
        try:
            # Create lock file
            with open(lock_file, 'w') as f:
                f.write(f"background_sync_{os.getpid()}")
            
            last_sync = datetime.now().isoformat()
            photos_sent = 0
            last_error = None
            
            print(f"[{datetime.now()}] Starting background sync with album URL: {self.album_url}")
            
            # Initialize scraper
            scraper = ICloudPhotoScraper(self.album_url, download_dir=self.photos_directory)
            
            # Scrape new photos
            print("Starting photo scraping...")
            new_photos = scraper.scrape_photos()
            print(f"Photo scraping completed. Found {len(new_photos)} new photos")
            
            if new_photos:
                # Initialize email sender
                email_sender = EmailSender(
                    os.getenv('SMTP_SERVER'),
                    int(os.getenv('SMTP_PORT', '587')),
                    os.getenv('SMTP_USERNAME'),
                    os.getenv('SMTP_PASSWORD')
                )
                
                # Send photos via email
                success = email_sender.send_photos_in_batches(
                    os.getenv('TO_EMAIL'), 
                    new_photos, 
                    batch_size=5
                )
                
                if success:
                    photos_sent = len(new_photos)
                    print(f"Successfully sent {photos_sent} photos")
                else:
                    last_error = "Failed to send some or all photos"
                    print(f"Error: {last_error}")
            else:
                print("No new photos found")
            
            self.update_status(last_sync=last_sync, last_error=last_error, photos_sent=photos_sent)
            self.last_sync = datetime.now()
            return True, f"Background sync completed. Found {len(new_photos)} new photos, sent {photos_sent}"
            
        except Exception as e:
            error_msg = f"Background sync error: {str(e)}"
            print(f"Error during background sync: {e}")
            self.update_status(last_sync=datetime.now().isoformat(), last_error=error_msg, photos_sent=0)
            return False, error_msg
        finally:
            # Clean up lock file
            if os.path.exists(lock_file):
                os.remove(lock_file)
    
    def _sync_worker(self):
        """Background thread that runs the sync process"""
        print(f"Background sync worker started. Checking every {self._format_interval(self.sync_interval // 60)}")
        
        while self.running:
            try:
                # Wait for the sync interval, checking every 30 seconds if we should stop
                wait_time = 0
                while wait_time < self.sync_interval and self.running:
                    time.sleep(30)
                    wait_time += 30
                
                if not self.running:
                    break
                
                # Run sync if we're still running
                if self.running:
                    success, message = self.run_sync_once()
                    if success:
                        print(f"[{datetime.now()}] {message}")
                    else:
                        print(f"[{datetime.now()}] Sync failed: {message}")
                
            except Exception as e:
                print(f"Error in sync worker: {e}")
                time.sleep(60)  # Wait a minute before trying again
    
    def start(self):
        """Start the background monitoring process"""
        if self.running:
            print("Background monitor is already running")
            return
        
        if not self.album_url:
            print("Error: ICLOUD_ALBUM_URL environment variable is required")
            return
        
        print("Starting SkylightSync Background Photo Monitor")
        print("=" * 50)
        print(f"Album URL: {self.album_url}")
        print(f"Photos Directory: {self.photos_directory}")
        print(f"Sync Interval: {self._format_interval(self.sync_interval // 60)}")
        print(f"Web UI available at: http://localhost:5003")
        print("=" * 50)
        
        self.running = True
        self.last_sync = datetime.now()
        
        # Update status to show background is active
        self.update_status()
        
        # Start the background sync thread
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        # Run initial sync
        print("Running initial sync...")
        success, message = self.run_sync_once()
        print(f"Initial sync: {message}")
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(60)  # Check every minute
                # Update status to show we're still active
                self.update_status()
        except KeyboardInterrupt:
            print("\nShutdown requested...")
            self.stop()
    
    def stop(self):
        """Stop the background monitoring process"""
        if not self.running:
            return
        
        print("Stopping background monitor...")
        self.running = False
        
        # Update status to show background is inactive
        self.update_status()
        
        # Wait for sync thread to finish
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        
        print("Background monitor stopped")

def main():
    # Load environment variables
    load_dotenv()
    
    # Create and start the background monitor
    monitor = BackgroundPhotoMonitor()
    monitor.start()

if __name__ == "__main__":
    main()