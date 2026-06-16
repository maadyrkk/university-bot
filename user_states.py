import json
from datetime import datetime
from db import db

def get_user_state(user_id):
    """Получить текущее состояние пользователя"""
    row = db.fetch_one("SELECT state, data FROM user_states WHERE user_id = ?", (user_id,))
    if row:
        state = row[0]
        data = json.loads(row[1]) if row[1] else {}
        return {'state': state, 'data': data}
    return {'state': None, 'data': {}}

def set_user_state(user_id, state, data=None):
    """Установить состояние пользователя"""
    json_data = json.dumps(data, ensure_ascii=False) if data else None
    db.execute('''
        INSERT INTO user_states (user_id, state, data, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            state = excluded.state,
            data = excluded.data,
            updated_at = excluded.updated_at
    ''', (user_id, state, json_data, datetime.now()))

def clear_user_state(user_id):
    """Очистить состояние пользователя"""
    db.execute("DELETE FROM user_states WHERE user_id = ?", (user_id,))

def get_all_users():
    """Получить всех пользователей"""
    return db.fetch_all("SELECT DISTINCT user_id FROM user_states")

def get_users_count():
    """Получить количество пользователей"""
    row = db.fetch_one("SELECT COUNT(DISTINCT user_id) FROM user_states")
    return row[0] if row else 0

def is_user_blacklisted(user_id):
    """Проверить, отписан ли пользователь от рассылки"""
    row = db.fetch_one("SELECT 1 FROM broadcast_blacklist WHERE user_id = ?", (user_id,))
    return row is not None

def add_to_blacklist(user_id):
    """Добавить пользователя в чёрный список рассылки"""
    try:
        db.execute("INSERT INTO broadcast_blacklist (user_id) VALUES (?)", (user_id,))
        return True
    except:
        return False

def remove_from_blacklist(user_id):
    """Удалить пользователя из чёрного списка рассылки"""
    cursor = db.execute("DELETE FROM broadcast_blacklist WHERE user_id = ?", (user_id,))
    return cursor.rowcount > 0

def get_broadcast_recipients():
    """Получить список пользователей для рассылки (не в чёрном списке)"""
    # Используем локальное соединение, а не глобальный db
    import sqlite3
    from config import DB_NAME
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT us.user_id 
        FROM user_states us
        LEFT JOIN broadcast_blacklist bb ON us.user_id = bb.user_id
        WHERE bb.user_id IS NULL
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]

def save_broadcast_history(admin_id, message, photo_attachment, recipients_count):
    """Сохранить историю рассылки"""
    db.execute('''
        INSERT INTO broadcast_history (admin_id, message, photo_attachment, recipients_count)
        VALUES (?, ?, ?, ?)
    ''', (admin_id, message, photo_attachment, recipients_count))

def get_broadcast_history(limit=10):
    """Получить историю рассылок"""
    return db.fetch_all('''
        SELECT id, admin_id, message, photo_attachment, recipients_count, sent_at
        FROM broadcast_history
        ORDER BY sent_at DESC
        LIMIT ?
    ''', (limit,))
