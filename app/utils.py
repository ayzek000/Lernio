from datetime import datetime, timedelta
import pytz
from app.supabase_client import get_supabase_client
import uuid

supabase = get_supabase_client()

def get_current_tashkent_time():
    """Возвращает текущее время в часовом поясе Ташкента"""
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tashkent_tz)

def log_activity(user_id, action, details=None):
    """Логирует действие пользователя в Supabase"""
    activity_data = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details
    }
    
    supabase.table('activity_logs').insert(activity_data).execute()