import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

class EmailSender:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_photos(self, recipient_email, photo_paths, subject=None):
        if not photo_paths:
            print("No photos to send")
            return False
        
        if subject is None:
            subject = f"New photos from iCloud album - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Email body
        body = f"""
        Hello,
        
        {len(photo_paths)} new photo(s) have been added to your iCloud shared album.
        Please find them attached to this email.
        
        Sent automatically by SkylightSync
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach photos
        for photo_path in photo_paths:
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(photo_path)}'
                    )
                    msg.attach(part)
            else:
                print(f"Warning: Photo not found: {photo_path}")
        
        # Send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            print(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_photos_in_batches(self, recipient_email, photo_paths, batch_size=5):
        """Send photos in batches to avoid large email sizes"""
        batches = [photo_paths[i:i + batch_size] for i in range(0, len(photo_paths), batch_size)]
        
        for i, batch in enumerate(batches):
            subject = f"Photos batch {i+1}/{len(batches)} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            success = self.send_photos(recipient_email, batch, subject)
            if not success:
                print(f"Failed to send batch {i+1}")
                return False
        
        return True