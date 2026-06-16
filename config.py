import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = 'university_bot.db'

def get_admin_ids():
    """Получение списка ID администраторов из переменной окружения"""
    ids_str = os.getenv('ADMIN_IDS', '')
    if not ids_str:
        return []
    if ',' in ids_str:
        return [int(x.strip()) for x in ids_str.split(',') if x.strip().isdigit()]
    if ids_str.isdigit():
        return [int(ids_str)]
    return []

def get_vk_config():
    """Получение конфигурации VK"""
    return {
        'token': os.getenv('VK_GROUP_TOKEN'),
        'group_id': int(os.getenv('VK_GROUP_ID', 0))
    }
