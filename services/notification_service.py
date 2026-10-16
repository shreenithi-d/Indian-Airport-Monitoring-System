from extensions import db
from models.notification import Notification

def create_notification(user_id, title, message, notification_type='system'):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def get_user_notifications(user_id, limit=20):
    return Notification.query.filter_by(user_id=user_id)\
        .order_by(Notification.created_at.desc())\
        .limit(limit).all()

def mark_notification_as_read(notification_id, user_id):
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False

def mark_all_notifications_as_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return True
