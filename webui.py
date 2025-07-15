#!/usr/bin/env python3

import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request, send_from_directory
from dotenv import load_dotenv
from icloud_scraper import ICloudPhotoScraper
from email_sender import EmailSender

# Load environment variables
load_dotenv()

# Configuration
ICLOUD_ALBUM_URL = os.getenv('ICLOUD_ALBUM_URL')
PHOTOS_DIRECTORY = os.getenv('PHOTOS_DIRECTORY', '/Users/m1/Pictures/Skylight')

# Global variables for scheduler
scheduler_active = False
scheduler_interval = 3600  # Default: 1 hour
scheduler_thread = None
last_scheduled_sync = None

def update_status(last_sync=None, last_error=None, photos_sent=None):
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
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)

def run_sync_once():
    """Run a single manual sync operation"""
    global last_scheduled_sync
    
    if not ICLOUD_ALBUM_URL:
        return False, "ICLOUD_ALBUM_URL not configured"
    
    # Create a lock file to prevent multiple instances
    lock_file = os.path.join('data', 'scraper.lock')
    background_lock_file = os.path.join('data', 'background_sync.lock')
    
    # Check if background sync is running
    if os.path.exists(background_lock_file):
        return False, "Background sync is running, please wait"
    
    # Check if another manual sync is running
    if os.path.exists(lock_file):
        return False, "Another manual sync is already running"
    
    try:
        # Create lock file
        with open(lock_file, 'w') as f:
            f.write(f"manual_sync_{os.getpid()}")
        
        last_sync = datetime.now().isoformat()
        photos_sent = 0
        last_error = None
        
        # Initialize scraper with environment variable
        print(f"Starting manual sync with album URL: {ICLOUD_ALBUM_URL}")
        scraper = ICloudPhotoScraper(ICLOUD_ALBUM_URL, download_dir=PHOTOS_DIRECTORY)
        
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
            else:
                last_error = "Failed to send some or all photos"
        
        update_status(last_sync=last_sync, last_error=last_error, photos_sent=photos_sent)
        last_scheduled_sync = datetime.now()
        return True, f"Manual sync completed. Found {len(new_photos)} new photos, sent {photos_sent}"
        
    except Exception as e:
        error_msg = f"Manual sync error: {str(e)}"
        update_status(last_sync=datetime.now().isoformat(), last_error=error_msg, photos_sent=0)
        return False, error_msg
    finally:
        # Clean up lock file
        if os.path.exists(lock_file):
            os.remove(lock_file)

def scheduler_worker():
    """Background thread that runs scheduled syncs"""
    global scheduler_active, scheduler_interval, last_scheduled_sync
    
    while scheduler_active:
        try:
            time.sleep(60)  # Check every minute
            
            if scheduler_active and last_scheduled_sync:
                next_sync = last_scheduled_sync + timedelta(seconds=scheduler_interval)
                if datetime.now() >= next_sync:
                    print(f"[{datetime.now()}] Running scheduled sync...")
                    success, message = run_sync_once()
                    if success:
                        print(f"[{datetime.now()}] Scheduled sync completed: {message}")
                    else:
                        print(f"[{datetime.now()}] Scheduled sync failed: {message}")
            elif scheduler_active and not last_scheduled_sync:
                # First scheduled sync
                print(f"[{datetime.now()}] Running first scheduled sync...")
                success, message = run_sync_once()
                if success:
                    print(f"[{datetime.now()}] First scheduled sync completed: {message}")
                else:
                    print(f"[{datetime.now()}] First scheduled sync failed: {message}")
                    
        except Exception as e:
            print(f"Scheduler error: {e}")
            time.sleep(60)

def get_background_status():
    """Check if background process is running and get its status"""
    status_file = os.path.join('data', 'status.json')
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
                return status.get('background_active', False), status
        except Exception:
            pass
    return False, {}

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>SkylightSync Control Panel</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .status-section, .control-section, .scheduler-section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .status-section { background-color: #f9f9f9; }
        .control-section { background-color: #e8f5e8; }
        .scheduler-section { background-color: #e8f0ff; }
        .status-item { margin: 10px 0; }
        .status-label { font-weight: bold; color: #666; }
        .status-value { color: #333; }
        .error { color: #d32f2f; }
        .success { color: #388e3c; }
        button { 
            background-color: #4CAF50; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px; 
            margin: 5px;
        }
        button:hover { background-color: #45a049; }
        button:disabled { background-color: #cccccc; cursor: not-allowed; }
        .danger { background-color: #f44336; }
        .danger:hover { background-color: #da190b; }
        .photos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .photo-item { text-align: center; }
        .photo-item img { max-width: 100%; height: 150px; object-fit: cover; border-radius: 5px; }
        .photo-item p { margin: 5px 0; font-size: 12px; color: #666; }
        .scheduler-controls { display: flex; align-items: center; gap: 10px; margin: 10px 0; }
        .scheduler-controls input, .scheduler-controls select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .scheduler-status { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .scheduler-active { background-color: #d4edda; color: #155724; }
        .scheduler-inactive { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌅 SkylightSync Control Panel</h1>
        
        <div class="status-section">
            <h2>📊 Sync Status</h2>
            <div id="status-content">Loading...</div>
        </div>
        
        <div class="scheduler-section">
            <h2>⏰ Background Process Status</h2>
            <div id="background-status" class="scheduler-status">
                <strong>Background Monitor:</strong> <span id="background-status-text">Loading...</span>
            </div>
            
            <div id="scheduler-section-old" style="display: none;">
                <h3>Web UI Scheduler (Legacy)</h3>
                <div id="scheduler-status" class="scheduler-status">
                    <strong>Status:</strong> <span id="scheduler-status-text">Loading...</span>
                </div>
                
                <div class="scheduler-controls">
                    <label>Interval:</label>
                    <input type="number" id="interval-hours" min="1" max="24" value="1" style="width: 60px;">
                    <label>hours</label>
                    <input type="number" id="interval-minutes" min="0" max="59" value="0" style="width: 60px;">
                    <label>minutes</label>
                </div>
                
                <button id="start-scheduler" onclick="startScheduler()">🚀 Start Web UI Scheduler</button>
                <button id="stop-scheduler" onclick="stopScheduler()" class="danger">⏹️ Stop Web UI Scheduler</button>
            </div>
        </div>
        
        <div class="control-section">
            <h2>🔄 Manual Controls</h2>
            <button onclick="triggerSync()" id="sync-btn">🔄 Sync Now</button>
            <button onclick="refreshStatus()">📊 Refresh Status</button>
        </div>
        
        <div class="status-section">
            <h2>📸 Recent Photos</h2>
            <div id="photos-content">Loading...</div>
        </div>
    </div>

    <script>
        let schedulerActive = false;
        let backgroundActive = false;
        
        function updateBackgroundStatus() {
            fetch('/background/status')
                .then(response => response.json())
                .then(data => {
                    backgroundActive = data.active;
                    const statusElement = document.getElementById('background-status');
                    const statusText = document.getElementById('background-status-text');
                    
                    if (data.active) {
                        statusElement.className = 'scheduler-status scheduler-active';
                        statusText.textContent = `Active (${data.interval_text})`;
                        if (data.next_sync) {
                            statusText.textContent += ` - Next sync: ${data.next_sync}`;
                        }
                        // Hide old scheduler section when background is active
                        document.getElementById('scheduler-section-old').style.display = 'none';
                    } else {
                        statusElement.className = 'scheduler-status scheduler-inactive';
                        statusText.textContent = 'Inactive - Run skylight_sync.py for background monitoring';
                        // Show old scheduler section when background is inactive
                        document.getElementById('scheduler-section-old').style.display = 'block';
                    }
                });
        }
        
        function updateSchedulerStatus() {
            fetch('/scheduler/status')
                .then(response => response.json())
                .then(data => {
                    schedulerActive = data.active;
                    const statusElement = document.getElementById('scheduler-status');
                    const statusText = document.getElementById('scheduler-status-text');
                    
                    if (data.active) {
                        statusElement.className = 'scheduler-status scheduler-active';
                        statusText.textContent = `Active (${data.interval_text})`;
                        if (data.next_sync) {
                            statusText.textContent += ` - Next sync: ${data.next_sync}`;
                        }
                        document.getElementById('start-scheduler').disabled = true;
                        document.getElementById('stop-scheduler').disabled = false;
                    } else {
                        statusElement.className = 'scheduler-status scheduler-inactive';
                        statusText.textContent = 'Inactive';
                        document.getElementById('start-scheduler').disabled = false;
                        document.getElementById('stop-scheduler').disabled = true;
                    }
                });
        }
        
        function startScheduler() {
            const hours = parseInt(document.getElementById('interval-hours').value) || 1;
            const minutes = parseInt(document.getElementById('interval-minutes').value) || 0;
            const intervalSeconds = (hours * 3600) + (minutes * 60);
            
            if (intervalSeconds < 300) {  // Minimum 5 minutes
                alert('Minimum interval is 5 minutes');
                return;
            }
            
            fetch('/scheduler/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interval: intervalSeconds })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Scheduler started successfully');
                    updateSchedulerStatus();
                } else {
                    alert('Failed to start scheduler: ' + data.message);
                }
            });
        }
        
        function stopScheduler() {
            fetch('/scheduler/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Scheduler stopped');
                        updateSchedulerStatus();
                    } else {
                        alert('Failed to stop scheduler: ' + data.message);
                    }
                });
        }
        
        function triggerSync() {
            const btn = document.getElementById('sync-btn');
            btn.disabled = true;
            btn.textContent = '🔄 Syncing...';
            
            fetch('/sync', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshStatus();
                    btn.disabled = false;
                    btn.textContent = '🔄 Sync Now';
                });
        }
        
        function refreshStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    html += '<div class="status-item"><span class="status-label">Last Sync:</span> <span class="status-value">' + (data.last_sync || 'Never') + '</span></div>';
                    html += '<div class="status-item"><span class="status-label">Photos Sent:</span> <span class="status-value">' + (data.photos_sent || 0) + '</span></div>';
                    if (data.last_error) {
                        html += '<div class="status-item"><span class="status-label">Last Error:</span> <span class="status-value error">' + data.last_error + '</span></div>';
                    } else {
                        html += '<div class="status-item"><span class="status-label">Status:</span> <span class="status-value success">✅ All good</span></div>';
                    }
                    document.getElementById('status-content').innerHTML = html;
                });
            
            fetch('/photos')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    if (data.photos && data.photos.length > 0) {
                        html = '<div class="photos-grid">';
                        data.photos.forEach(photo => {
                            html += '<div class="photo-item">';
                            html += '<img src="/downloads/' + photo.filename + '" alt="' + photo.filename + '">';
                            html += '<p>' + photo.filename + '</p>';
                            html += '</div>';
                        });
                        html += '</div>';
                    } else {
                        html = '<p>No photos available</p>';
                    }
                    document.getElementById('photos-content').innerHTML = html;
                });
        }
        
        // Auto-refresh every 10 seconds
        setInterval(() => {
            refreshStatus();
            updateBackgroundStatus();
            updateSchedulerStatus();
        }, 10000);
        
        // Initial load
        refreshStatus();
        updateBackgroundStatus();
        updateSchedulerStatus();
    </script>
</body>
</html>
    ''')

@app.route('/background/status')
def background_status():
    background_active, status_data = get_background_status()
    
    next_sync = None
    interval_text = "Unknown"
    
    if background_active and status_data:
        # Get interval from status data
        interval_minutes = status_data.get('sync_interval_minutes', 60)
        hours = interval_minutes // 60
        minutes = interval_minutes % 60
        interval_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Get next sync time
        next_sync = status_data.get('next_sync')
        if next_sync:
            next_sync = datetime.fromisoformat(next_sync).strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'active': background_active,
        'interval_text': interval_text,
        'next_sync': next_sync
    })

@app.route('/scheduler/status')
def scheduler_status():
    global scheduler_active, scheduler_interval, last_scheduled_sync
    
    next_sync = None
    if scheduler_active and last_scheduled_sync:
        next_sync_time = last_scheduled_sync + timedelta(seconds=scheduler_interval)
        next_sync = next_sync_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert interval to human readable format
    hours = scheduler_interval // 3600
    minutes = (scheduler_interval % 3600) // 60
    interval_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    return jsonify({
        'active': scheduler_active,
        'interval': scheduler_interval,
        'interval_text': interval_text,
        'next_sync': next_sync
    })

@app.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    global scheduler_active, scheduler_interval, scheduler_thread, last_scheduled_sync
    
    try:
        data = request.get_json()
        new_interval = data.get('interval', 3600)
        
        if new_interval < 300:  # Minimum 5 minutes
            return jsonify({'success': False, 'message': 'Minimum interval is 5 minutes'})
        
        # Stop existing scheduler if running
        if scheduler_active:
            scheduler_active = False
            if scheduler_thread:
                scheduler_thread.join(timeout=5)
        
        # Start new scheduler
        scheduler_active = True
        scheduler_interval = new_interval
        last_scheduled_sync = None  # Reset to trigger immediate first sync
        
        scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
        scheduler_thread.start()
        
        return jsonify({'success': True, 'message': 'Scheduler started'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    global scheduler_active, scheduler_thread
    
    try:
        scheduler_active = False
        if scheduler_thread:
            scheduler_thread.join(timeout=5)
        
        return jsonify({'success': True, 'message': 'Scheduler stopped'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/sync', methods=['POST'])
def manual_sync():
    try:
        # Run sync in a separate thread to avoid blocking the web request
        def run_sync():
            run_sync_once()
        
        sync_thread = threading.Thread(target=run_sync, daemon=True)
        sync_thread.start()
        
        return jsonify({
            'message': 'Manual sync triggered',
            'status': 'started',
            'time': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'message': f'Failed to trigger sync: {str(e)}',
            'status': 'error',
            'time': datetime.now().isoformat()
        })

@app.route('/status')
def status():
    status_file = os.path.join('data', 'status.json')
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            try:
                return jsonify(json.load(f))
            except Exception:
                pass
    
    return jsonify({
        'last_sync': None,
        'last_error': None,
        'photos_sent': 0
    })

@app.route('/photos')
def photos():
    photos_list = []
    if os.path.exists(PHOTOS_DIRECTORY):
        for filename in os.listdir(PHOTOS_DIRECTORY):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                photos_list.append({
                    'filename': filename,
                    'path': os.path.join(PHOTOS_DIRECTORY, filename)
                })
    
    # Sort by filename (newest first based on timestamp in filename)
    photos_list.sort(key=lambda x: x['filename'], reverse=True)
    
    return jsonify({'photos': photos_list[:12]})  # Return latest 12 photos

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(PHOTOS_DIRECTORY, filename)

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    print("Starting SkylightSync Web UI...")
    print("Access the control panel at: http://localhost:5003")
    app.run(host='0.0.0.0', port=5003, debug=False) 