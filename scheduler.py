import threading
import time
import sqlite3
from datetime import datetime
from vk_api.utils import get_random_id
from utils import send_message
from config import DB_NAME
from user_states import get_broadcast_recipients
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_db_connection():
    """Создаёт отдельное соединение с БД для текущего потока"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_scheduler_db():
    """Создание таблиц для планировщика (вызывается из главного потока)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        scheduled_time TIMESTAMP NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        recipients_count INTEGER DEFAULT 0,
        error_message TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scheduled_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        broadcast_id INTEGER NOT NULL,
        message_text TEXT,
        photo_attachment TEXT,
        message_order INTEGER DEFAULT 0,
        FOREIGN KEY (broadcast_id) REFERENCES scheduled_broadcasts(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Таблицы планировщика созданы")


def add_scheduled_broadcast(admin_id, messages_with_photos, scheduled_time_str):
    """
    Добавить отложенную рассылку
    messages_with_photos: список кортежей (текст, фото_вложение_или_None)
    scheduled_time_str: строка в формате 'YYYY-MM-DD HH:MM:SS'
    """
    try:
        scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%d %H:%M:%S')
        if scheduled_time < datetime.now():
            return False, "❌ Время рассылки должно быть в будущем!"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scheduled_broadcasts (admin_id, scheduled_time)
            VALUES (?, ?)
        ''', (admin_id, scheduled_time))
        broadcast_id = cursor.lastrowid
        
        for order, (msg_text, photo) in enumerate(messages_with_photos):
            # Если текст None или пустая строка, но есть фото — сохраняем пустую строку
            text_to_save = msg_text if msg_text and msg_text.strip() != '' else ""
            
            cursor.execute('''
                INSERT INTO scheduled_messages (broadcast_id, message_text, photo_attachment, message_order)
                VALUES (?, ?, ?, ?)
            ''', (broadcast_id, text_to_save, photo, order))
        
        conn.commit()
        conn.close()
        
        return True, f"✅ Рассылка запланирована на {scheduled_time.strftime('%d.%m.%Y %H:%M:%S')} (сообщений: {len(messages_with_photos)})"
    
    except ValueError:
        return False, "❌ Неверный формат даты! Используйте: ГГГГ-ММ-ДД ЧЧ:ММ:СС"


def get_pending_broadcasts():
    """Получить все неотправленные рассылки, время которых уже наступило"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sb.id, sb.admin_id, sb.scheduled_time,
               sm.message_text, sm.photo_attachment, sm.message_order
        FROM scheduled_broadcasts sb
        JOIN scheduled_messages sm ON sb.id = sm.broadcast_id
        WHERE sb.status = 'pending' AND sb.scheduled_time <= ?
        ORDER BY sb.id, sm.message_order
    ''', (now,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Преобразуем sqlite3.Row в обычные списки
    return [list(row) for row in rows]


def update_broadcast_status(broadcast_id, status, recipients_count=0, error_msg=None):
    """Обновить статус рассылки"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status == 'completed':
        cursor.execute('''
            UPDATE scheduled_broadcasts 
            SET status = ?, sent_at = ?, recipients_count = ?
            WHERE id = ?
        ''', (status, now, recipients_count, broadcast_id))
    elif status == 'failed':
        cursor.execute('''
            UPDATE scheduled_broadcasts 
            SET status = ?, sent_at = ?, error_message = ?
            WHERE id = ?
        ''', (status, now, error_msg, broadcast_id))
    else:
        cursor.execute('''
            UPDATE scheduled_broadcasts 
            SET status = ?
            WHERE id = ?
        ''', (status, broadcast_id))
    
    conn.commit()
    conn.close()


def process_scheduled_broadcasts(vk):
    """Обработчик отложенных рассылок (запускать в отдельном потоке)"""
    pending = get_pending_broadcasts()
    if not pending:
        return
    
    # Группируем сообщения по broadcast_id
    broadcasts_dict = {}
    for row in pending:
        bid = row[0]
        if bid not in broadcasts_dict:
            broadcasts_dict[bid] = {
                'admin_id': row[1],
                'scheduled_time': row[2],
                'messages': []
            }
        broadcasts_dict[bid]['messages'].append({
            'text': row[3] if row[3] is not None else "",
            'photo': row[4],
            'order': row[5]
        })
    
    for broadcast_id, data in broadcasts_dict.items():
        try:
            recipients = get_broadcast_recipients()
            if not recipients:
                update_broadcast_status(broadcast_id, 'failed', 0, 'Нет получателей')
                continue
            
            total = len(recipients)
            total_messages = len(data['messages'])
            success_count = 0
            
            for msg_data in sorted(data['messages'], key=lambda x: x['order']):
                has_text = msg_data['text'] and msg_data['text'].strip() != ''
                has_photo = msg_data['photo'] is not None
                
                # Если нет ни текста, ни фото — пропускаем
                if not has_text and not has_photo:
                    print(f"⚠️ Пропущено пустое сообщение в рассылке #{broadcast_id}")
                    continue
                
                for user_id in recipients:
                    try:
                        if has_photo and not has_text:
                            # Только фото (без текста) — отправляем пробел как сообщение
                            vk.messages.send(
                                peer_id=user_id,
                                message=" ",
                                random_id=get_random_id(),
                                attachment=msg_data['photo']
                            )
                        elif has_photo and has_text:
                            # Фото + текст
                            vk.messages.send(
                                peer_id=user_id,
                                message=msg_data['text'],
                                random_id=get_random_id(),
                                attachment=msg_data['photo']
                            )
                        else:
                            # Только текст
                            vk.messages.send(
                                peer_id=user_id,
                                message=msg_data['text'],
                                random_id=get_random_id()
                            )
                        success_count += 1
                        time.sleep(0.34)
                    except Exception as e:
                        print(f"Ошибка отправки пользователю {user_id}: {e}")
                
                if total_messages > 1:
                    time.sleep(5)
            
            update_broadcast_status(broadcast_id, 'completed', success_count)
            print(f"✅ Отложенная рассылка #{broadcast_id} выполнена. Отправлено: {success_count}/{total * total_messages}")
            
        except Exception as e:
            update_broadcast_status(broadcast_id, 'failed', 0, str(e))
            print(f"❌ Ошибка отложенной рассылки #{broadcast_id}: {e}")


def list_scheduled_broadcasts():
    """Показать список запланированных рассылок с содержимым сообщений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем список рассылок
    cursor.execute('''
        SELECT id, admin_id, scheduled_time, status, sent_at, recipients_count
        FROM scheduled_broadcasts
        ORDER BY scheduled_time DESC
        LIMIT 10
    ''')
    
    broadcasts = cursor.fetchall()
    
    if not broadcasts:
        conn.close()
        return "📋 Нет запланированных рассылок."
    
    result = "📋 **ЗАПЛАНИРОВАННЫЕ РАССЫЛКИ**\n\n"
    
    for broadcast in broadcasts:
        bid, admin_id, sched_time, status, sent_at, count = broadcast
        sched_time_str = sched_time[:16] if sched_time else "неизвестно"
        
        status_emoji = {
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(status, '❓')
        
        result += f"{status_emoji} **Рассылка #{bid}**\n"
        result += f"   📅 Запланирована: {sched_time_str}\n"
        result += f"   👤 Админ: {admin_id}\n"
        if status == 'completed':
            result += f"   📊 Отправлено: {count}\n"
        
        # Получаем сообщения для этой рассылки
        cursor.execute('''
            SELECT message_text, photo_attachment, message_order
            FROM scheduled_messages
            WHERE broadcast_id = ?
            ORDER BY message_order
        ''', (bid,))
        
        messages = cursor.fetchall()
        
        if messages:
            result += f"   📨 **Сообщения ({len(messages)}):**\n"
            for msg in messages:
                msg_text, msg_photo, msg_order = msg
                has_photo = "📷" if msg_photo else ""
                if msg_text and msg_text.strip() != '':
                    # Есть текст
                    preview = msg_text[:50] + "..." if len(msg_text) > 50 else msg_text
                    result += f"      {msg_order+1}. {has_photo} {preview}\n"
                else:
                    # Только фото
                    result += f"      {msg_order+1}. {has_photo} (только фото)\n"
        else:
            result += f"   📨 Сообщения: (нет)\n"
        
        result += "\n"
    
    conn.close()
    return result


def cancel_scheduled_broadcast(broadcast_id):
    """Отмена запланированной рассылки"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT status FROM scheduled_broadcasts WHERE id = ?', (broadcast_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, f"❌ Рассылка #{broadcast_id} не найдена"
    
    if row[0] != 'pending':
        conn.close()
        return False, f"❌ Рассылка #{broadcast_id} уже {row[0]} (нельзя отменить)"
    
    cursor.execute('UPDATE scheduled_broadcasts SET status = ? WHERE id = ?', ('cancelled', broadcast_id))
    conn.commit()
    conn.close()
    
    return True, f"✅ Рассылка #{broadcast_id} отменена"


def run_scheduler_loop(vk):
    """Запуск бесконечного цикла проверки отложенных рассылок"""
    while True:
        try:
            process_scheduled_broadcasts(vk)
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
        time.sleep(30)


def start_scheduler_thread(vk):
    """Запустить планировщик в отдельном потоке"""
    thread = threading.Thread(target=run_scheduler_loop, args=(vk,), daemon=True)
    thread.start()
    print("Планировщик отложенных рассылок запущен")
    return thread
