from models.database import Notification, db
import traceback

def create_in_app_notification(user_id, title, message, type='system'):
    """Create a new in-app notification in the database"""
    try:
        new_notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type
        )
        db.session.add(new_notif)
        db.session.commit()
        print(f"✅ Notification created: {title}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating notification: {e}")
        traceback.print_exc()
        return False
