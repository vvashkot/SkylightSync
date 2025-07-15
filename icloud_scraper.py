import time
import os
import json
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.chrome.service import Service

class ICloudPhotoScraper:
    def __init__(self, album_url, download_dir='/Users/m1/Pictures/Skylight', data_dir='data'):
        self.album_url = album_url
        self.download_dir = download_dir
        self.data_dir = data_dir
        self.processed_photos_file = os.path.join(data_dir, 'processed_photos.json')
        self.processed_urls_file = os.path.join(data_dir, 'processed_urls.json')
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        self.processed_photos = self.load_processed_photos()
        self.processed_urls = self.load_processed_urls()
        
        # Migrate existing processed photos to URL database if needed
        self.migrate_existing_urls()
    
    def load_processed_photos(self):
        if os.path.exists(self.processed_photos_file):
            with open(self.processed_photos_file, 'r') as f:
                return json.load(f)
        return {}
    
    def load_processed_urls(self):
        """Load the processed URLs database"""
        if os.path.exists(self.processed_urls_file):
            with open(self.processed_urls_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_processed_photos(self):
        with open(self.processed_photos_file, 'w') as f:
            json.dump(self.processed_photos, f, indent=2)
    
    def save_processed_urls(self):
        """Save the processed URLs database"""
        with open(self.processed_urls_file, 'w') as f:
            json.dump(self.processed_urls, f, indent=2)
    
    def normalize_url(self, url):
        """
        Normalize iCloud URL by extracting the core photo identifier
        iCloud URLs have this pattern: https://cvws.icloud-content.com/S/XXXXX/FILENAME.JPG?params
        We'll use the path part (S/XXXXX/FILENAME.JPG) as the identifier
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            # Extract the path which contains the stable photo identifier
            path = parsed.path
            # Remove leading slash and use path as identifier
            return path.lstrip('/')
        except:
            # Fallback: use the original URL
            return url
    
    def is_url_processed(self, url):
        """Check if we've already processed this URL (or a variant of it)"""
        normalized_url = self.normalize_url(url)
        return normalized_url in self.processed_urls
    
    def mark_url_processed(self, url, photo_hash):
        """Mark a URL as processed and link it to the photo hash"""
        normalized_url = self.normalize_url(url)
        self.processed_urls[normalized_url] = {
            'photo_hash': photo_hash,
            'original_url': url,
            'processed_at': datetime.now().isoformat()
        }
    
    def migrate_existing_urls(self):
        """Migrate existing processed photos to URL database"""
        if not self.processed_urls and self.processed_photos:
            print("Migrating existing processed photos to URL database...")
            migrated_count = 0
            for photo_hash, photo_data in self.processed_photos.items():
                if 'url' in photo_data:
                    self.mark_url_processed(photo_data['url'], photo_hash)
                    migrated_count += 1
            
            if migrated_count > 0:
                print(f"Migrated {migrated_count} URLs to URL database")
                self.save_processed_urls()
    
    def get_photo_hash(self, photo_data):
        return hashlib.md5(photo_data).hexdigest()
    
    def setup_driver(self):
        import tempfile
        import uuid
        import time
        
        # Create a unique temporary directory for this Chrome instance
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_data_{uuid.uuid4().hex[:8]}_{int(time.time())}_")
        
        chrome_options = Options()
        # Run in regular mode for better compatibility on local machine
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Use the unique temporary directory for this Chrome instance
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')
        
        # Basic Chrome options for stability
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--remote-debugging-port=0')  # Use random port
        
        # Store the temp directory for cleanup
        self.temp_chrome_dir = temp_dir
        print(f"Chrome temp directory: {temp_dir}")
        
        # Create the WebDriver with unique user data directory
        # Use chromedriver from PATH (installed via brew)
        driver = webdriver.Chrome(options=chrome_options)
        
        return driver
    
    def wait_for_images_to_load(self, driver, timeout=10):
        """Wait for images to load after scrolling"""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: len(d.find_elements(By.TAG_NAME, "img")) > 0
            )
        except TimeoutException:
            print("No images found after waiting")
    
    def navigate_carousel_and_collect_images(self, driver):
        """Navigate through the photo carousel to collect all image URLs"""
        print("Starting carousel navigation to collect image URLs...")
        print("Note: 'New URL' means a URL not seen in this session, not necessarily a new photo")
        
        # Wait for initial page load (reduced from 5s to 2s)
        time.sleep(2)
        
        # First, try to click on the first photo to enter carousel view
        print("Looking for first photo to click...")
        try:
            # Look for clickable view buttons (these are the actual clickable elements)
            view_buttons = driver.find_elements(By.CSS_SELECTOR, "[role='button'][aria-label*='of']")
            if view_buttons:
                print(f"Found {len(view_buttons)} view buttons, clicking first one...")
                view_buttons[0].click()
                time.sleep(1)  # Reduced from 3s to 1s
            else:
                # Fallback: try clicking on any clickable photo container
                photo_containers = driver.find_elements(By.CSS_SELECTOR, ".x-stream-photo-grid-item-view, [class*='photo'], [class*='grid-item']")
                if photo_containers:
                    print(f"Found {len(photo_containers)} photo containers, clicking first one...")
                    photo_containers[0].click()
                    time.sleep(1)  # Reduced from 3s to 1s
                else:
                    print("No clickable photo elements found")
                    return []
        except Exception as e:
            print(f"Error clicking first photo: {e}")
            return []
        
        all_images = set()
        photo_count = 0
        first_photo_url = None
        consecutive_duplicates = 0
        
        print("Navigating through photos... (progress will update in place)")
        
        # Navigate through the carousel
        while True:
                
            try:
                # Wait for the current photo to load (reduced from 2s to 0.25s)
                time.sleep(0.25)
                
                # Find the current photo in carousel view
                carousel_images = driver.find_elements(By.CSS_SELECTOR, "img[src*='icloud']")
                if not carousel_images:
                    print(f"\rNo images found in carousel view at photo {photo_count + 1}")
                    break
                
                # Get the current photo URL
                current_image = carousel_images[0]  # Usually the main image is first
                image_url = current_image.get_attribute('src')
                
                if image_url and image_url not in all_images:
                    all_images.add(image_url)
                    consecutive_duplicates = 0
                    
                    # Store the first photo URL for loop detection
                    if first_photo_url is None:
                        first_photo_url = image_url
                elif image_url:
                    consecutive_duplicates += 1
                    
                    # If we've seen too many consecutive duplicates, we might be in a loop
                    if consecutive_duplicates > 10:
                        print(f"\rToo many consecutive duplicate URLs, likely in a loop. Stopping...")
                        break
                
                # Check if we've looped back to the first photo
                if first_photo_url and image_url == first_photo_url and photo_count > 0:
                    print(f"\rReached first photo again (loop detected), stopping...")
                    break
                
                # Update progress in place
                print(f"\rProgress: Photo {photo_count + 1} | Unique URLs: {len(all_images)} | Consecutive duplicates: {consecutive_duplicates}", end='', flush=True)
                
                # Try to navigate to the next photo (optimized)
                try:
                    # Look for next button or use arrow key
                    next_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Next'], .next, [data-testid='next']")
                    next_button.click()
                    # Reduced wait after click
                    time.sleep(0.1)
                except:
                    # Try using arrow key as fallback
                    from selenium.webdriver.common.keys import Keys
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_RIGHT)
                    # Reduced wait after arrow key
                    time.sleep(0.1)
                
                photo_count += 1
                
                # Safety check to prevent infinite loops
                if photo_count > 5000:  # Reasonable limit for most albums
                    print(f"\rReached maximum photo limit (5000), stopping navigation...")
                    break
                
            except Exception as e:
                print(f"\rError navigating photo {photo_count + 1}: {e}")
                break
        
        print(f"\nFinished carousel navigation. Navigated {photo_count} photos, found {len(all_images)} unique URLs")
        return list(all_images)
    
    def scrape_photos(self):
        # Create a lock file to prevent multiple instances
        lock_file = os.path.join(self.data_dir, 'scraper.lock')
        if os.path.exists(lock_file):
            # Check if the process is still running
            try:
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                import psutil
                if psutil.pid_exists(pid):
                    print(f"Another scraper instance is already running (PID: {pid}). Skipping...")
                    return []
                else:
                    print(f"Stale lock file found (PID: {pid} not running). Removing...")
                    os.remove(lock_file)
            except (ValueError, FileNotFoundError):
                print("Invalid lock file found. Removing...")
                os.remove(lock_file)
        
        # Create lock file
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        driver = self.setup_driver()
        new_photos = []
        try:
            print(f"Loading album: {self.album_url}")
            driver.get(self.album_url)
            
            # Navigate carousel and collect all image URLs
            image_urls = self.navigate_carousel_and_collect_images(driver)
            
            if not image_urls:
                print("No images found!")
                return new_photos
            
            print(f"Found {len(image_urls)} unique URLs. Checking for new photos...")
            print(f"Already processed {len(self.processed_photos)} photos and {len(self.processed_urls)} URLs in database")
            
            # Pre-filter URLs we've already processed
            unprocessed_urls = []
            url_skipped_count = 0
            
            for url in image_urls:
                if self.is_url_processed(url):
                    url_skipped_count += 1
                else:
                    unprocessed_urls.append(url)
            
            print(f"URL pre-filtering: {len(unprocessed_urls)} URLs need checking, {url_skipped_count} URLs already processed")
            
            if not unprocessed_urls:
                print("All URLs have been processed before - no downloads needed!")
                self.save_processed_urls()
                return new_photos
            
            # Download only unprocessed URLs
            seen_hashes = set(self.processed_photos.keys())
            new_photos_count = 0
            skipped_count = 0
            videos_skipped = 0
            errors_count = 0
            
            print("Checking unprocessed URLs for new content... (progress will update in place)")
            
            for idx, image_url in enumerate(unprocessed_urls):
                try:
                    # Update progress in place
                    print(f"\rProgress: {idx+1}/{len(unprocessed_urls)} | New: {new_photos_count} | Skipped: {skipped_count} | Videos: {videos_skipped} | Errors: {errors_count}", end='', flush=True)
                    
                    response = requests.get(image_url, timeout=30)
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # Skip videos
                        if any(video_type in content_type for video_type in ['video/', 'mp4', 'mov', 'avi', 'wmv', 'flv', 'webm']):
                            videos_skipped += 1
                            # Still mark video URLs as processed to avoid checking them again
                            self.mark_url_processed(image_url, None)
                            continue
                        if any(ext in image_url.lower() for ext in ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv']):
                            videos_skipped += 1
                            # Still mark video URLs as processed to avoid checking them again
                            self.mark_url_processed(image_url, None)
                            continue
                        
                        photo_hash = self.get_photo_hash(response.content)
                        
                        # Always mark URL as processed, regardless of whether photo is new
                        self.mark_url_processed(image_url, photo_hash)
                        
                        if photo_hash not in seen_hashes:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"photo_{timestamp}_{idx}.jpg"
                            filepath = os.path.join(self.download_dir, filename)
                            
                            # Save to intended directory
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            # If file was saved to Downloads, move it
                            downloads_dir = os.path.expanduser('~/Downloads')
                            downloaded_file = os.path.join(downloads_dir, filename)
                            if os.path.exists(downloaded_file):
                                import shutil
                                shutil.move(downloaded_file, filepath)
                                print(f"\nMoved {downloaded_file} to {filepath}")
                            
                            self.processed_photos[photo_hash] = {
                                'filename': filename,
                                'timestamp': timestamp,
                                'url': image_url,
                                'emailed': False
                            }
                            new_photos.append(filepath)
                            seen_hashes.add(photo_hash)
                            new_photos_count += 1
                            print(f"\n✓ NEW PHOTO: {filename}")
                        else:
                            skipped_count += 1
                    else:
                        errors_count += 1
                        # Don't mark failed URLs as processed - we might want to retry them
                except Exception as e:
                    errors_count += 1
                    # Don't mark failed URLs as processed - we might want to retry them
                    continue
            
            print(f"\nDownload phase complete: {new_photos_count} new photos, {skipped_count} already processed, {videos_skipped} videos skipped, {errors_count} errors")
            print(f"Total efficiency: {url_skipped_count} URLs skipped by pre-filtering, {len(unprocessed_urls)} URLs actually checked")
            
            self.save_processed_photos()
            self.save_processed_urls()
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            driver.quit()
            
            # Clean up temporary Chrome directory
            if hasattr(self, 'temp_chrome_dir') and os.path.exists(self.temp_chrome_dir):
                import shutil
                try:
                    shutil.rmtree(self.temp_chrome_dir)
                    print(f"Cleaned up temporary Chrome directory: {self.temp_chrome_dir}")
                except Exception as e:
                    print(f"Warning: Could not clean up temporary Chrome directory: {e}")
            
            # Clean up lock file
            lock_file = os.path.join(self.data_dir, 'scraper.lock')
            if os.path.exists(lock_file):
                os.remove(lock_file)
        return new_photos

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get album URL from .env file
    album_url = os.getenv('ICLOUD_ALBUM_URL')
    
    if not album_url:
        print("No ICLOUD_ALBUM_URL found in .env file. Exiting.")
        exit(1)
    
    print("Starting iCloud Photo Scraper...")
    scraper = ICloudPhotoScraper(album_url)
    new_photos = scraper.scrape_photos()
    
    print(f"Scraping completed. Downloaded {len(new_photos)} new photos.")
    if new_photos:
        print("New photos downloaded:")
        for photo in new_photos:
            print(f"  - {photo}")
    
    # Email sync step (always run, regardless of new photos)
    print("Starting email sync check...")
    from email_sender import EmailSender
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')
    print(f"Email config: SMTP={smtp_server}, Sender={sender_email}, Recipient={recipient_email}")
    if smtp_server and sender_email and sender_password and recipient_email:
        emailer = EmailSender(smtp_server, smtp_port, sender_email, sender_password)
        
        # Get all photos that haven't been emailed yet
        unemailed_photos = []
        total_photos = len(scraper.processed_photos)
        print(f"Checking {total_photos} photos in database for email status...")
        for photo_hash, photo_data in scraper.processed_photos.items():
            if not photo_data.get('emailed', False):
                photo_path = os.path.join(scraper.download_dir, photo_data['filename'])
                if os.path.exists(photo_path):
                    unemailed_photos.append(photo_path)
                    print(f"Found unemailed photo: {photo_data['filename']}")
        
        print(f"Found {len(unemailed_photos)} unemailed photos")
        if unemailed_photos:
            print(f"Sending {len(unemailed_photos)} unemailed photos to {recipient_email}...")
            success = emailer.send_photos_in_batches(recipient_email, unemailed_photos, batch_size=5)
            if success:
                # Mark all photos as emailed
                for photo_hash in scraper.processed_photos:
                    if not scraper.processed_photos[photo_hash].get('emailed', False):
                        scraper.processed_photos[photo_hash]['emailed'] = True
                scraper.save_processed_photos()
                print("All photos marked as emailed in database.")
            else:
                print("Email sending failed, photos not marked as emailed.")
        else:
            print("No unemailed photos found.")
    else:
        print("Email config missing in .env, skipping email sync.")
    
    if not new_photos:
        print("No new photos found.")