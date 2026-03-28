from flask import current_app as app, render_template_string
from flask_mail import Message
import firebase_admin
from firebase_admin import messaging
import os

def send_push_notification(user, title, body, data=None):
    """Send a push notification via Firebase Cloud Messaging"""
    if not user.fcm_token or not user.push_enabled:
        return False
    
    try:
        # Check if Firebase is initialized
        if not firebase_admin._apps:
            print("⚠️ Cannot send push: Firebase Admin not initialized.")
            return False

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=user.fcm_token,
        )
        
        response = messaging.send(message)
        print(f"✅ Push sent successfully: {response}")
        return True
    except Exception as e:
        print(f"❌ Error sending push notification: {e}")
        return False

def send_scan_result_email(user, scan_result):
    """Send a scan result summary email via Flask-Mail"""
    if not user.email_enabled:
        return False
    
    try:
        from app import mail
        
        subject = f"SafePose: Scan Result Update ({scan_result.prediction.capitalize()})"
        
        # Simple HTML template for the email
        html_content = f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #6366f1;">SafePose Scan Completed</h2>
                    <p>Hello {user.name},</p>
                    <p>Your recent motion analysis scan is complete. Here are the results:</p>
                    
                    <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>Result:</strong> {scan_result.prediction.capitalize()}</p>
                        <p><strong>Confidence:</strong> {int(scan_result.confidence * 100)}%</p>
                        <p><strong>Time:</strong> {scan_result.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                    
                    <p>Open the SafePose app to view your full history and insights.</p>
                    
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
                    <p style="font-size: 12px; color: #999;">
                        This is an automated notification from SafePose. 
                        You can disable email alerts in your profile settings.
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=html_content
        )
        
        mail.send(msg)
        print(f"✅ Email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
