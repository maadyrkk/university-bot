from db import db
from models import (
    get_education_levels, add_education_level, delete_education_level, edit_education_level,
    get_faculties, add_faculty, delete_faculty, edit_faculty,
    get_all_subjects, add_subject, delete_subject, edit_subject,
    get_all_entrance_exams, add_entrance_exam, delete_entrance_exam, edit_entrance_exam,
    get_all_directions, get_all_programs, get_all_faq,
    add_faq, delete_faq, edit_faq, get_stats,
    add_direction, delete_direction, edit_direction, get_direction_by_id,
    get_all_faculties_list, get_all_levels_list,
    get_direction_subjects, get_direction_exams,
    add_required_subject, remove_required_subject,
    add_elective_subject, remove_elective_subject,
    add_required_exam, remove_required_exam,
    get_all_subjects_list, get_all_exams_list,
    get_all_programs_list, get_program_by_id, add_program, edit_program, delete_program,
    get_all_directions_for_select,
    get_faq_by_category, get_faq_categories
)
from user_states import set_user_state, get_users_count, get_broadcast_recipients, get_all_users, is_user_blacklisted
from keyboards import (
    build_crud_keyboard, build_admin_menu_keyboard, build_directions_crud_keyboard, 
    build_broadcast_keyboard, build_scheduled_compose_keyboard, build_faq_admin_keyboard
)

from utils import send_message
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
import os

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def show_directions_list_for_selection(vk, peer_id):
    """Показать список направлений для выбора"""
    directions = get_all_directions()
    if not directions:
        send_message(vk, peer_id, "📋 Список направлений пуст")
        return False
    
    message = "📋 **СПИСОК НАПРАВЛЕНИЙ**\n\n"
    for row in directions:
        dir_id, code, name, desc, faculty, level = row[0], row[1], row[2], row[3], row[4], row[5]
        message += f"{dir_id}. {code} - {name}\n   {faculty} | {level}\n"
        if desc:
            message += f"   📖 {desc[:80]}...\n"
        message += "\n"
        if len(message) > 3500:
            send_message(vk, peer_id, message)
            message = ""
    if message:
        send_message(vk, peer_id, message)
    return True

def show_directions_list_for_programs(vk, peer_id):
    """Показать список направлений для выбора при добавлении программы"""
    directions = get_all_directions_for_select()
    if not directions:
        send_message(vk, peer_id, "📋 Список направлений пуст. Сначала добавьте направления!")
        return False
    
    message = "📋 **СПИСОК НАПРАВЛЕНИЙ ДЛЯ ПРОГРАММ**\n\n"
    for row in directions:
        dir_id, code, name, faculty, level = row[0], row[1], row[2], row[3], row[4]
        message += f"{dir_id}. {code} - {name}\n   🏛 {faculty} | 📚 {level}\n\n"
        if len(message) > 3500:
            send_message(vk, peer_id, message)
            message = ""
    if message:
        send_message(vk, peer_id, message)
    return True


# ============================================================
# ОСНОВНАЯ АДМИН-ПАНЕЛЬ
# ============================================================

def show_admin_stats(vk, peer_id):
    """Показать общую статистику"""
    stats = get_stats()
    users_count = get_users_count()
    subscribed_count = len(get_broadcast_recipients())
    unsubscribed_count = db.fetch_one('SELECT COUNT(*) FROM broadcast_blacklist')[0]
    
    message = (
        "📊 **СТАТИСТИКА БАЗЫ ДАННЫХ**\n\n"
        f"📚 Уровней образования: {stats['levels']}\n"
        f"🏛 Факультетов: {stats['faculties']}\n"
        f"📖 Предметов ЕГЭ: {stats['subjects']}\n"
        f"🎓 Вступительных испытаний (ВИ): {stats['entrance_exams']}\n"
        f"📋 Направлений: {stats['directions']}\n"
        f"📚 Программ обучения: {stats['programs']}\n"
        f"❓ Вопросов FAQ: {stats['faq']}\n"
        f"👥 Пользователей: {users_count}\n"
        f"✅ Подписаны на рассылку: {subscribed_count}\n"
        f"❌ Отписались: {unsubscribed_count}"
    )
    send_message(vk, peer_id, message)


# ============================================================
# УРОВНИ ОБРАЗОВАНИЯ CRUD
# ============================================================

def show_admin_levels(vk, peer_id, user_id):
    levels = get_education_levels()
    if not levels:
        send_message(vk, peer_id, "Список уровней пуст")
        return
    message = "📚 **УРОВНИ ОБРАЗОВАНИЯ**\n\n"
    for row in levels:
        lvl_id, name = row[0], row[1]
        message += f"{lvl_id}. {name}\n"
    send_message(vk, peer_id, message)
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_crud_keyboard())
    set_user_state(user_id, 'admin_levels_menu')

def handle_admin_levels(vk, peer_id, user_id, text, state_data):
    if text == "➕ Добавить":
        send_message(vk, peer_id, "Введите название нового уровня образования:")
        set_user_state(user_id, 'admin_levels_add')
    elif text == "✏️ Редактировать":
        send_message(vk, peer_id, "Введите ID уровня для редактирования:")
        set_user_state(user_id, 'admin_levels_edit_id')
    elif text == "❌ Удалить":
        send_message(vk, peer_id, "Введите ID уровня для удаления:")
        set_user_state(user_id, 'admin_levels_delete')
    elif text == "📋 Список":
        show_admin_levels(vk, peer_id, user_id)
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
    return True

def handle_admin_levels_add(vk, peer_id, user_id, text):
    success, msg = add_education_level(text)
    send_message(vk, peer_id, msg)
    show_admin_levels(vk, peer_id, user_id)
    return True

def handle_admin_levels_edit_id(vk, peer_id, user_id, text):
    try:
        level_id = int(text)
        set_user_state(user_id, 'admin_levels_edit_name', {'id': level_id})
        send_message(vk, peer_id, f"Введите новое название для уровня ID {level_id}:")
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID уровня)")
        set_user_state(user_id, 'admin_levels_menu')
        show_admin_levels(vk, peer_id, user_id)
    return True

def handle_admin_levels_edit_name(vk, peer_id, user_id, text, state_data):
    level_id = state_data.get('id')
    success, msg = edit_education_level(level_id, text)
    send_message(vk, peer_id, msg)
    show_admin_levels(vk, peer_id, user_id)
    return True

def handle_admin_levels_delete(vk, peer_id, user_id, text):
    try:
        level_id = int(text)
        success, msg = delete_education_level(level_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID уровня)")
    show_admin_levels(vk, peer_id, user_id)
    return True


# ============================================================
# ФАКУЛЬТЕТЫ CRUD
# ============================================================

def show_admin_faculties(vk, peer_id, user_id):
    faculties = get_faculties()
    if not faculties:
        send_message(vk, peer_id, "Список факультетов пуст")
        return
    message = "🏛 **ФАКУЛЬТЕТЫ**\n\n"
    for row in faculties:
        fac_id, name = row[0], row[1]
        message += f"{fac_id}. {name}\n"
    send_message(vk, peer_id, message)
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_crud_keyboard())
    set_user_state(user_id, 'admin_faculties_menu')

def handle_admin_faculties(vk, peer_id, user_id, text, state_data):
    if text == "➕ Добавить":
        send_message(vk, peer_id, "Введите название нового факультета:")
        set_user_state(user_id, 'admin_faculties_add')
    elif text == "✏️ Редактировать":
        send_message(vk, peer_id, "Введите ID факультета для редактирования:")
        set_user_state(user_id, 'admin_faculties_edit_id')
    elif text == "❌ Удалить":
        send_message(vk, peer_id, "Введите ID факультета для удаления:")
        set_user_state(user_id, 'admin_faculties_delete')
    elif text == "📋 Список":
        show_admin_faculties(vk, peer_id, user_id)
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
    return True

def handle_admin_faculties_add(vk, peer_id, user_id, text):
    success, msg = add_faculty(text)
    send_message(vk, peer_id, msg)
    show_admin_faculties(vk, peer_id, user_id)
    return True

def handle_admin_faculties_edit_id(vk, peer_id, user_id, text):
    try:
        fac_id = int(text)
        set_user_state(user_id, 'admin_faculties_edit_name', {'id': fac_id})
        send_message(vk, peer_id, f"Введите новое название для факультета ID {fac_id}:")
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID факультета)")
        set_user_state(user_id, 'admin_faculties_menu')
        show_admin_faculties(vk, peer_id, user_id)
    return True

def handle_admin_faculties_edit_name(vk, peer_id, user_id, text, state_data):
    fac_id = state_data.get('id')
    success, msg = edit_faculty(fac_id, text)
    send_message(vk, peer_id, msg)
    show_admin_faculties(vk, peer_id, user_id)
    return True

def handle_admin_faculties_delete(vk, peer_id, user_id, text):
    try:
        fac_id = int(text)
        success, msg = delete_faculty(fac_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID факультета)")
    show_admin_faculties(vk, peer_id, user_id)
    return True


# ============================================================
# ПРЕДМЕТЫ ЕГЭ CRUD
# ============================================================

def show_admin_subjects(vk, peer_id, user_id):
    subjects = get_all_subjects()
    if not subjects:
        send_message(vk, peer_id, "Список предметов ЕГЭ пуст")
        return
    message = "📖 **ПРЕДМЕТЫ ЕГЭ**\n\n"
    for row in subjects:
        subj_id, name, min_score = row[0], row[1], row[2]
        message += f"{subj_id}. {name} (мин. {min_score} баллов)\n"
    send_message(vk, peer_id, message)
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_crud_keyboard())
    set_user_state(user_id, 'admin_subjects_menu')

def handle_admin_subjects(vk, peer_id, user_id, text, state_data):
    if text == "➕ Добавить":
        send_message(vk, peer_id, "Введите название предмета и минимальный балл через запятую\nПример: Физика,41")
        set_user_state(user_id, 'admin_subjects_add')
    elif text == "✏️ Редактировать":
        send_message(vk, peer_id, "Введите ID предмета для редактирования:")
        set_user_state(user_id, 'admin_subjects_edit_id')
    elif text == "❌ Удалить":
        send_message(vk, peer_id, "Введите ID предмета для удаления:")
        set_user_state(user_id, 'admin_subjects_delete')
    elif text == "📋 Список":
        show_admin_subjects(vk, peer_id, user_id)
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
    return True

def handle_admin_subjects_add(vk, peer_id, user_id, text):
    try:
        parts = text.split(',')
        name = parts[0].strip()
        min_score = int(parts[1].strip()) if len(parts) > 1 else 40
        success, msg = add_subject(name, min_score)
        send_message(vk, peer_id, msg)
    except Exception as e:
        send_message(vk, peer_id, f"Ошибка: {e}\nФормат: Название, минимальный балл")
    show_admin_subjects(vk, peer_id, user_id)
    return True

def handle_admin_subjects_edit_id(vk, peer_id, user_id, text):
    try:
        subj_id = int(text)
        set_user_state(user_id, 'admin_subjects_edit_data', {'id': subj_id})
        send_message(vk, peer_id, f"Введите новое название и минимальный балл для предмета ID {subj_id} через запятую\nПример: Физика,41")
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID предмета)")
        set_user_state(user_id, 'admin_subjects_menu')
        show_admin_subjects(vk, peer_id, user_id)
    return True

def handle_admin_subjects_edit_data(vk, peer_id, user_id, text, state_data):
    subj_id = state_data.get('id')
    try:
        parts = text.split(',')
        name = parts[0].strip()
        min_score = int(parts[1].strip()) if len(parts) > 1 else 40
        success, msg = edit_subject(subj_id, name, min_score)
        send_message(vk, peer_id, msg)
    except Exception as e:
        send_message(vk, peer_id, f"Ошибка: {e}")
    show_admin_subjects(vk, peer_id, user_id)
    return True

def handle_admin_subjects_delete(vk, peer_id, user_id, text):
    try:
        subj_id = int(text)
        success, msg = delete_subject(subj_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID предмета)")
    show_admin_subjects(vk, peer_id, user_id)
    return True


# ============================================================
# ВСТУПИТЕЛЬНЫЕ ИСПЫТАНИЯ CRUD
# ============================================================

def show_admin_entrance_exams(vk, peer_id, user_id):
    exams = get_all_entrance_exams()
    if not exams:
        send_message(vk, peer_id, "Список ВИ пуст")
        return
    message = "🎓 **ВСТУПИТЕЛЬНЫЕ ИСПЫТАНИЯ (ВИ)**\n\n"
    for row in exams:
        exam_id, name, min_score, desc = row[0], row[1], row[2], row[3]
        message += f"{exam_id}. {name} (мин. {min_score} баллов)\n"
        if desc:
            message += f"   📝 {desc}\n"
        message += "\n"
    send_message(vk, peer_id, message)
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_crud_keyboard())
    set_user_state(user_id, 'admin_exams_menu')

def handle_admin_exams(vk, peer_id, user_id, text, state_data):
    if text == "➕ Добавить":
        send_message(vk, peer_id, "Введите: название, минимальный балл, описание (опционально)\nПример: Общая психология,40,Профессиональное испытание")
        set_user_state(user_id, 'admin_exams_add')
    elif text == "✏️ Редактировать":
        send_message(vk, peer_id, "Введите ID ВИ для редактирования:")
        set_user_state(user_id, 'admin_exams_edit_id')
    elif text == "❌ Удалить":
        send_message(vk, peer_id, "Введите ID ВИ для удаления:")
        set_user_state(user_id, 'admin_exams_delete')
    elif text == "📋 Список":
        show_admin_entrance_exams(vk, peer_id, user_id)
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
    return True

def handle_admin_exams_add(vk, peer_id, user_id, text):
    try:
        parts = [p.strip() for p in text.split(',')]
        name = parts[0]
        min_score = int(parts[1]) if len(parts) > 1 else 40
        description = parts[2] if len(parts) > 2 else None
        success, msg = add_entrance_exam(name, min_score, description)
        send_message(vk, peer_id, msg)
    except Exception as e:
        send_message(vk, peer_id, f"Ошибка: {e}")
    show_admin_entrance_exams(vk, peer_id, user_id)
    return True

def handle_admin_exams_edit_id(vk, peer_id, user_id, text):
    try:
        exam_id = int(text)
        set_user_state(user_id, 'admin_exams_edit_data', {'id': exam_id})
        send_message(vk, peer_id, f"Введите новые данные для ВИ ID {exam_id} через запятую\nФормат: название, минимальный балл, описание")
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID ВИ)")
        set_user_state(user_id, 'admin_exams_menu')
        show_admin_entrance_exams(vk, peer_id, user_id)
    return True

def handle_admin_exams_edit_data(vk, peer_id, user_id, text, state_data):
    exam_id = state_data.get('id')
    try:
        parts = [p.strip() for p in text.split(',')]
        name = parts[0]
        min_score = int(parts[1]) if len(parts) > 1 else 40
        description = parts[2] if len(parts) > 2 else None
        success, msg = edit_entrance_exam(exam_id, name, min_score, description)
        send_message(vk, peer_id, msg)
    except Exception as e:
        send_message(vk, peer_id, f"Ошибка: {e}")
    show_admin_entrance_exams(vk, peer_id, user_id)
    return True

def handle_admin_exams_delete(vk, peer_id, user_id, text):
    try:
        exam_id = int(text)
        success, msg = delete_entrance_exam(exam_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "Ошибка: введите число (ID ВИ)")
    show_admin_entrance_exams(vk, peer_id, user_id)
    return True


# ============================================================
# НАПРАВЛЕНИЯ
# ============================================================

def show_admin_directions(vk, peer_id, user_id):
    """Показать меню управления направлениями"""
    send_message(vk, peer_id, "📋 **УПРАВЛЕНИЕ НАПРАВЛЕНИЯМИ**\n\nВыберите действие:", keyboard=build_directions_crud_keyboard())
    set_user_state(user_id, 'admin_directions_menu')


def handle_admin_directions(vk, peer_id, user_id, text, state_data):
    if text == "➕ Добавить":
        # Показываем список факультетов
        faculties = get_all_faculties_list()
        if not faculties:
            send_message(vk, peer_id, "❌ Сначала добавьте факультеты!")
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        message = "🏛 **ВЫБЕРИТЕ ФАКУЛЬТЕТ**\n\n"
        for fac in faculties:
            message += f"{fac[0]}. {fac[1]}\n"
        
        send_message(vk, peer_id, message)
        send_message(vk, peer_id, "Введите ID факультета:")
        set_user_state(user_id, 'admin_directions_add_faculty')
        return True
    
    elif text == "✏️ Редактировать":
        send_message(vk, peer_id, "Введите ID направления для редактирования:")
        set_user_state(user_id, 'admin_directions_edit_id')
        return True

    elif text == "📚 Обязательные предметы":
        handle_admin_directions_required_subjects(vk, peer_id, user_id, text, {})
        return True
    
    elif text == "📖 Предметы на выбор":
        handle_admin_directions_elective_subjects(vk, peer_id, user_id, text, {})
        return True
    
    elif text == "🎓 ВИ":
        handle_admin_directions_exams(vk, peer_id, user_id, text, {})
        return True
    
    elif text == "❌ Удалить":
        send_message(vk, peer_id, "Введите ID направления для удаления:")
        set_user_state(user_id, 'admin_directions_delete')
        return True
    
    elif text == "📋 Список":
        directions = get_all_directions()
        if not directions:
            send_message(vk, peer_id, "📋 Список направлений пуст")
        else:
            message = "📋 **НАПРАВЛЕНИЯ ПОДГОТОВКИ**\n\n"
            for row in directions:
                dir_id, code, name, desc, faculty, level = row[0], row[1], row[2], row[3], row[4], row[5]
                message += f"{dir_id}. {code} - {name}\n   {faculty} | {level}\n"
                if desc:
                    message += f"   📖 {desc[:100]}...\n"
                message += "\n"
                if len(message) > 3500:
                    send_message(vk, peer_id, message)
                    message = ""
            if message:
                send_message(vk, peer_id, message)
        return True
    
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
        return True
    
    return False


def handle_admin_directions_add_faculty(vk, peer_id, user_id, text, state_data):
    try:
        faculty_id = int(text)
        faculties = get_all_faculties_list()
        faculty_exists = any(fac[0] == faculty_id for fac in faculties)
        
        if not faculty_exists:
            send_message(vk, peer_id, "❌ Факультет с таким ID не найден!")
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        # Показываем список уровней
        levels = get_all_levels_list()
        if not levels:
            send_message(vk, peer_id, "❌ Сначала добавьте уровни образования!")
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        message = "📚 **ВЫБЕРИТЕ УРОВЕНЬ ОБРАЗОВАНИЯ**\n\n"
        for lvl in levels:
            message += f"{lvl[0]}. {lvl[1]}\n"
        
        send_message(vk, peer_id, message)
        send_message(vk, peer_id, "Введите ID уровня образования:")
        set_user_state(user_id, 'admin_directions_add_level', {'faculty_id': faculty_id})
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID факультета)")
        return True


def handle_admin_directions_add_level(vk, peer_id, user_id, text, state_data):
    try:
        level_id = int(text)
        levels = get_all_levels_list()
        level_exists = any(lvl[0] == level_id for lvl in levels)
        
        if not level_exists:
            send_message(vk, peer_id, "❌ Уровень с таким ID не найден!")
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        faculty_id = state_data.get('faculty_id')
        
        send_message(vk, peer_id, "📝 Введите КОД направления (например: 01.03.02):")
        set_user_state(user_id, 'admin_directions_add_code', {
            'faculty_id': faculty_id,
            'level_id': level_id
        })
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID уровня)")
        return True


def handle_admin_directions_add_code(vk, peer_id, user_id, text, state_data):
    code = text.strip()
    if not code:
        send_message(vk, peer_id, "❌ Код не может быть пустым!")
        return True
    
    send_message(vk, peer_id, "📝 Введите НАЗВАНИЕ направления:")
    set_user_state(user_id, 'admin_directions_add_name', {
        'faculty_id': state_data.get('faculty_id'),
        'level_id': state_data.get('level_id'),
        'code': code
    })
    return True


def handle_admin_directions_add_name(vk, peer_id, user_id, text, state_data):
    name = text.strip()
    if not name:
        send_message(vk, peer_id, "❌ Название не может быть пустым!")
        return True
    
    send_message(vk, peer_id, "📝 Введите ОПИСАНИЕ направления (или '-' если без описания):")
    set_user_state(user_id, 'admin_directions_add_desc', {
        'faculty_id': state_data.get('faculty_id'),
        'level_id': state_data.get('level_id'),
        'code': state_data.get('code'),
        'name': name
    })
    return True


def handle_admin_directions_add_desc(vk, peer_id, user_id, text, state_data):
    description = text.strip()
    if description == '-':
        description = ''
    
    faculty_id = state_data.get('faculty_id')
    level_id = state_data.get('level_id')
    code = state_data.get('code')
    name = state_data.get('name')
    
    success, msg = add_direction(code, name, description, faculty_id, level_id)
    send_message(vk, peer_id, msg)
    
    show_admin_directions(vk, peer_id, user_id)
    return True


def handle_admin_directions_edit_id(vk, peer_id, user_id, text, state_data):
    try:
        direction_id = int(text)
        direction = get_direction_by_id(direction_id)
        
        if not direction:
            send_message(vk, peer_id, "❌ Направление с таким ID не найдено!")
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        # Получаем списки факультетов и уровней
        faculties = get_all_faculties_list()
        levels = get_all_levels_list()
        
        set_user_state(user_id, 'admin_directions_edit_data', {'direction_id': direction_id})
        
        message = f"✏️ **РЕДАКТИРОВАНИЕ НАПРАВЛЕНИЯ**\n\n"
        message += f"Текущие данные:\n"
        message += f"ID: {direction[0]}\n"
        message += f"Код: {direction[1]}\n"
        message += f"Название: {direction[2]}\n"
        message += f"Описание: {direction[3] or '—'}\n"
        message += f"ID факультета: {direction[4]} ({direction[6]})\n"
        message += f"ID уровня: {direction[5]} ({direction[7]})\n\n"
        
        # Добавляем список доступных уровней
        message += "📚 **ДОСТУПНЫЕ УРОВНИ ОБРАЗОВАНИЯ:**\n"
        for lvl in levels:
            message += f"  • {lvl[0]} - {lvl[1]}\n"
        
        message += "\n🏛 **ДОСТУПНЫЕ ФАКУЛЬТЕТЫ:**\n"
        for fac in faculties:
            message += f"  • {fac[0]} - {fac[1]}\n"
        
        message += f"\n📝 **Введите новые данные в формате:**\n"
        message += f"ID_УРОВНЯ,ID_ФАКУЛЬТЕТА,КОД,НАЗВАНИЕ,ОПИСАНИЕ\n\n"
        message += f"**Пример:** {direction[5]},{direction[4]},{direction[1]},{direction[2]},Новое описание"
        
        # Разбиваем сообщение, если оно слишком длинное
        if len(message) > 4000:
            # Отправляем основную информацию
            main_msg = f"✏️ **РЕДАКТИРОВАНИЕ НАПРАВЛЕНИЯ**\n\n"
            main_msg += f"Текущие данные:\n"
            main_msg += f"ID: {direction[0]}\n"
            main_msg += f"Код: {direction[1]}\n"
            main_msg += f"Название: {direction[2]}\n"
            main_msg += f"Описание: {direction[3] or '—'}\n"
            main_msg += f"ID факультета: {direction[4]} ({direction[6]})\n"
            main_msg += f"ID уровня: {direction[5]} ({direction[7]})\n\n"
            main_msg += f"📝 Введите новые данные в формате:\n"
            main_msg += f"ID_УРОВНЯ,ID_ФАКУЛЬТЕТА,КОД,НАЗВАНИЕ,ОПИСАНИЕ\n\n"
            main_msg += f"**Пример:** {direction[5]},{direction[4]},{direction[1]},{direction[2]},Новое описание"
            
            send_message(vk, peer_id, main_msg)
            
            # Отправляем списки отдельно
            levels_msg = "📚 **ДОСТУПНЫЕ УРОВНИ ОБРАЗОВАНИЯ:**\n"
            for lvl in levels:
                levels_msg += f"  • {lvl[0]} - {lvl[1]}\n"
            send_message(vk, peer_id, levels_msg)
            
            faculties_msg = "🏛 **ДОСТУПНЫЕ ФАКУЛЬТЕТЫ:**\n"
            for fac in faculties:
                faculties_msg += f"  • {fac[0]} - {fac[1]}\n"
            send_message(vk, peer_id, faculties_msg)
        else:
            send_message(vk, peer_id, message)
        
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID направления)")
        return True


def handle_admin_directions_edit_data(vk, peer_id, user_id, text, state_data):
    try:
        parts = text.split(',')
        if len(parts) < 5:
            send_message(vk, peer_id, "❌ Неверный формат! Используйте: ID_УРОВНЯ,ID_ФАКУЛЬТЕТА,КОД,НАЗВАНИЕ,ОПИСАНИЕ")
            send_message(vk, peer_id, "Пример: 1,2,01.03.02,Прикладная математика,Описание направления")
            return True
        
        level_id = int(parts[0].strip())
        faculty_id = int(parts[1].strip())
        code = parts[2].strip()
        name = parts[3].strip()
        description = parts[4].strip()
        if description == '-':
            description = ''
        
        # Проверяем существование факультета и уровня
        faculties = get_all_faculties_list()
        levels = get_all_levels_list()
        
        if not any(fac[0] == faculty_id for fac in faculties):
            send_message(vk, peer_id, "❌ Факультет с таким ID не найден!")
            return True
        
        if not any(lvl[0] == level_id for lvl in levels):
            send_message(vk, peer_id, "❌ Уровень с таким ID не найден!")
            return True
        
        direction_id = state_data.get('direction_id')
        success, msg = edit_direction(direction_id, code, name, description, faculty_id, level_id)
        send_message(vk, peer_id, msg)
        
        show_admin_directions(vk, peer_id, user_id)
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Ошибка: ID уровня и ID факультета должны быть числами")
        return True
    except Exception as e:
        send_message(vk, peer_id, f"❌ Ошибка: {e}")
        return True


def handle_admin_directions_delete(vk, peer_id, user_id, text, state_data):
    try:
        direction_id = int(text)
        success, msg = delete_direction(direction_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID направления)")
    
    show_admin_directions(vk, peer_id, user_id)
    return True


# ============================================================
# УПРАВЛЕНИЕ ОБЯЗАТЕЛЬНЫМИ ПРЕДМЕТАМИ
# ============================================================

def handle_admin_directions_required_subjects(vk, peer_id, user_id, text, state_data):
    """Управление обязательными предметами направления"""
    if 'step' not in state_data:
        # Показываем список направлений
        show_directions_list_for_selection(vk, peer_id)
        send_message(vk, peer_id, "Введите ID направления для управления обязательными предметами:\n(или нажмите ◀ Назад для возврата)")
        set_user_state(user_id, 'admin_directions_req_subj_id')
        return True
    
    elif state_data.get('step') == 'waiting_action':
        if text == "➕ Добавить":
            subjects = get_all_subjects_list()
            if not subjects:
                send_message(vk, peer_id, "❌ Сначала добавьте предметы в разделе 'Предметы ЕГЭ'!")
                handle_admin_directions_required_subjects(vk, peer_id, user_id, '', {})
                return True
            
            direction_id = state_data.get('direction_id')
            # Сортируем предметы по ID
            sorted_subjects = sorted(subjects, key=lambda x: x[0])
            
            message = f"📖 **ДОСТУПНЫЕ ПРЕДМЕТЫ**\n\n"
            for subj in sorted_subjects:
                message += f"{subj[0]}. {subj[1]} (мин. {subj[2]} баллов)\n"
            
            send_message(vk, peer_id, message)
            send_message(vk, peer_id, "Введите ID предмета для добавления:\n(или нажмите ◀ Назад для возврата)")
            set_user_state(user_id, 'admin_directions_req_subj_add', {'direction_id': direction_id})
            return True
        
        elif text == "❌ Удалить":
            direction_id = state_data.get('direction_id')
            subjects = get_direction_subjects(direction_id)
            
            if not subjects['required']:
                send_message(vk, peer_id, "У этого направления нет обязательных предметов!")
                handle_admin_directions_required_subjects(vk, peer_id, user_id, '', {})
                return True
            
            # Сортируем предметы по ID
            sorted_subjects = sorted(subjects['required'], key=lambda x: x[0])
            
            message = f"📖 **ОБЯЗАТЕЛЬНЫЕ ПРЕДМЕТЫ НАПРАВЛЕНИЯ**\n\n"
            for subj in sorted_subjects:
                message += f"{subj[0]}. {subj[1]} (мин. {subj[2]} баллов)\n"
            
            send_message(vk, peer_id, message)
            send_message(vk, peer_id, "Введите ID предмета для удаления:\n(или нажмите ◀ Назад для возврата)")
            set_user_state(user_id, 'admin_directions_req_subj_remove', {'direction_id': direction_id})
            return True
        
        elif text == "📋 Список":
            direction_id = state_data.get('direction_id')
            subjects = get_direction_subjects(direction_id)
            
            if not subjects['required']:
                send_message(vk, peer_id, "У этого направления нет обязательных предметов.")
            else:
                # Сортируем предметы по ID
                sorted_subjects = sorted(subjects['required'], key=lambda x: x[0])
                message = f"📖 **ОБЯЗАТЕЛЬНЫЕ ПРЕДМЕТЫ**\n\n"
                for subj in sorted_subjects:
                    message += f"{subj[0]}. {subj[1]} (мин. {subj[2]} баллов)\n"
                send_message(vk, peer_id, message)
            return True
        
        elif text == "◀ Назад":
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        return True


# ============================================================
# УПРАВЛЕНИЕ ПРЕДМЕТАМИ НА ВЫБОР
# ============================================================

def handle_admin_directions_elective_subjects(vk, peer_id, user_id, text, state_data):
    """Управление предметами на выбор направления"""
    if 'step' not in state_data:
        # Показываем список направлений
        show_directions_list_for_selection(vk, peer_id)
        send_message(vk, peer_id, "Введите ID направления для управления предметами на выбор:\n(или нажмите ◀ Назад для возврата)")
        set_user_state(user_id, 'admin_directions_el_subj_id')
        return True
    
    elif state_data.get('step') == 'waiting_action':
        if text == "➕ Добавить":
            subjects = get_all_subjects_list()
            if not subjects:
                send_message(vk, peer_id, "❌ Сначала добавьте предметы в разделе 'Предметы ЕГЭ'!")
                handle_admin_directions_elective_subjects(vk, peer_id, user_id, '', {})
                return True
            
            direction_id = state_data.get('direction_id')
            # Сортируем предметы по ID
            sorted_subjects = sorted(subjects, key=lambda x: x[0])
            
            message = f"📖 **ДОСТУПНЫЕ ПРЕДМЕТЫ**\n\n"
            for subj in sorted_subjects:
                message += f"{subj[0]}. {subj[1]} (мин. {subj[2]} баллов)\n"
            
            send_message(vk, peer_id, message)
            send_message(vk, peer_id, "Введите ID предмета для добавления:\n(или нажмите ◀ Назад для возврата)")
            set_user_state(user_id, 'admin_directions_el_subj_add', {'direction_id': direction_id})
            return True
        
        elif text == "❌ Удалить":
            direction_id = state_data.get('direction_id')
            subjects = get_direction_subjects(direction_id)
            
            if not subjects['elective']:
                send_message(vk, peer_id, "У этого направления нет предметов на выбор!")
                handle_admin_directions_elective_subjects(vk, peer_id, user_id, '', {})
                return True
            
            # Сортируем предметы по ID
            sorted_subjects = sorted(subjects['elective'], key=lambda x: x[0])
            
            message = f"📖 **ПРЕДМЕТЫ НА ВЫБОР НАПРАВЛЕНИЯ**\n\n"
            for subj in sorted_subjects:
                message += f"{subj[0]}. {subj[1]} (мин. {subj[2]} баллов)\n"
            
            send_message(vk, peer_id, message)
            send_message(vk, peer_id, "Введите ID предмета для удаления:\n(или нажмите ◀ Назад для возврата)")
            set_user_state(user_id, 'admin_directions_el_subj_remove', {'direction_id': direction_id})
            return True
        
        elif text == "📋 Список":
            direction_id = state_data.get('direction_id')
            subjects = get_direction_subjects(direction_id)
            
            if not subjects['elective']:
                send_message(vk, peer_id, "У этого направления нет предметов на выбор.")
            else:
                # Сортируем предметы по ID
                sorted_subjects = sorted(subjects['elective'], key=lambda x: x[0])
                message = f"📖 **ПРЕДМЕТЫ НА ВЫБОР**\n\n"
                for subj in sorted_subjects:
                    message += f"{subj[0]}. {subj[1]} (мин. {subj[2]} баллов)\n"
                send_message(vk, peer_id, message)
            return True
        
        elif text == "◀ Назад":
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        return True


# ============================================================
# УПРАВЛЕНИЕ ВСТУПИТЕЛЬНЫМИ ИСПЫТАНИЯМИ
# ============================================================

def handle_admin_directions_exams(vk, peer_id, user_id, text, state_data):
    """Управление ВИ направления"""
    if 'step' not in state_data:
        # Показываем список направлений
        show_directions_list_for_selection(vk, peer_id)
        send_message(vk, peer_id, "Введите ID направления для управления ВИ:\n(или нажмите ◀ Назад для возврата)")
        set_user_state(user_id, 'admin_directions_exams_id')
        return True
    
    elif state_data.get('step') == 'waiting_action':
        if text == "➕ Добавить":
            exams = get_all_exams_list()
            if not exams:
                send_message(vk, peer_id, "❌ Сначала добавьте ВИ в разделе 'ВИ (вступительные)'!")
                handle_admin_directions_exams(vk, peer_id, user_id, '', {})
                return True
            
            direction_id = state_data.get('direction_id')
            # Сортируем ВИ по ID
            sorted_exams = sorted(exams, key=lambda x: x[0])
            
            message = f"🎓 **ДОСТУПНЫЕ ВСТУПИТЕЛЬНЫЕ ИСПЫТАНИЯ**\n\n"
            for exam in sorted_exams:
                message += f"{exam[0]}. {exam[1]} (мин. {exam[2]} баллов)\n"
            
            send_message(vk, peer_id, message)
            send_message(vk, peer_id, "Введите ID ВИ для добавления:\n(или нажмите ◀ Назад для возврата)")
            set_user_state(user_id, 'admin_directions_exams_add', {'direction_id': direction_id})
            return True
        
        elif text == "❌ Удалить":
            direction_id = state_data.get('direction_id')
            exams = get_direction_exams(direction_id)
            
            if not exams:
                send_message(vk, peer_id, "У этого направления нет ВИ!")
                handle_admin_directions_exams(vk, peer_id, user_id, '', {})
                return True
            
            # Сортируем ВИ по ID
            sorted_exams = sorted(exams, key=lambda x: x[0])
            
            message = f"🎓 **ВСТУПИТЕЛЬНЫЕ ИСПЫТАНИЯ НАПРАВЛЕНИЯ**\n\n"
            for exam in sorted_exams:
                message += f"{exam[0]}. {exam[1]} (мин. {exam[2]} баллов)\n"
                if exam[3]:
                    message += f"   📝 {exam[3]}\n"
            
            send_message(vk, peer_id, message)
            send_message(vk, peer_id, "Введите ID ВИ для удаления:\n(или нажмите ◀ Назад для возврата)")
            set_user_state(user_id, 'admin_directions_exams_remove', {'direction_id': direction_id})
            return True
        
        elif text == "📋 Список":
            direction_id = state_data.get('direction_id')
            exams = get_direction_exams(direction_id)
            
            if not exams:
                send_message(vk, peer_id, "У этого направления нет ВИ.")
            else:
                # Сортируем ВИ по ID
                sorted_exams = sorted(exams, key=lambda x: x[0])
                message = f"🎓 **ВСТУПИТЕЛЬНЫЕ ИСПЫТАНИЯ**\n\n"
                for exam in sorted_exams:
                    message += f"{exam[0]}. {exam[1]} (мин. {exam[2]} баллов)\n"
                    if exam[3]:
                        message += f"   📝 {exam[3]}\n"
                send_message(vk, peer_id, message)
            return True
        
        elif text == "◀ Назад":
            show_admin_directions(vk, peer_id, user_id)
            return True
        
        return True


# ============================================================
# ОБРАБОТЧИКИ ДЛЯ ВВОДА ID НАПРАВЛЕНИЯ (С ПОДДЕРЖКОЙ ◀ НАЗАД)
# ============================================================

def handle_admin_directions_req_subj_id(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        show_admin_directions(vk, peer_id, user_id)
        return True
    
    try:
        direction_id = int(text)
        direction = get_direction_by_id(direction_id)
        if not direction:
            send_message(vk, peer_id, "❌ Направление с таким ID не найдено!")
            show_directions_list_for_selection(vk, peer_id)
            send_message(vk, peer_id, "Введите ID направления для управления обязательными предметами:\n(или нажмите ◀ Назад для возврата)")
            return True
        
        send_message(vk, peer_id, f"📚 **УПРАВЛЕНИЕ ОБЯЗАТЕЛЬНЫМИ ПРЕДМЕТАМИ**\n\nНаправление: {direction[1]} - {direction[2]}\n\nВыберите действие:", 
                     keyboard=build_crud_keyboard())
        set_user_state(user_id, 'admin_directions_req_subj_menu', {'direction_id': direction_id, 'step': 'waiting_action'})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID направления) или нажмите ◀ Назад")
        return True


def handle_admin_directions_el_subj_id(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        show_admin_directions(vk, peer_id, user_id)
        return True
    
    try:
        direction_id = int(text)
        direction = get_direction_by_id(direction_id)
        if not direction:
            send_message(vk, peer_id, "❌ Направление с таким ID не найдено!")
            show_directions_list_for_selection(vk, peer_id)
            send_message(vk, peer_id, "Введите ID направления для управления предметами на выбор:\n(или нажмите ◀ Назад для возврата)")
            return True
        
        send_message(vk, peer_id, f"📖 **УПРАВЛЕНИЕ ПРЕДМЕТАМИ НА ВЫБОР**\n\nНаправление: {direction[1]} - {direction[2]}\n\nВыберите действие:", 
                     keyboard=build_crud_keyboard())
        set_user_state(user_id, 'admin_directions_el_subj_menu', {'direction_id': direction_id, 'step': 'waiting_action'})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID направления) или нажмите ◀ Назад")
        return True


def handle_admin_directions_exams_id(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        show_admin_directions(vk, peer_id, user_id)
        return True
    
    try:
        direction_id = int(text)
        direction = get_direction_by_id(direction_id)
        if not direction:
            send_message(vk, peer_id, "❌ Направление с таким ID не найдено!")
            show_directions_list_for_selection(vk, peer_id)
            send_message(vk, peer_id, "Введите ID направления для управления ВИ:\n(или нажмите ◀ Назад для возврата)")
            return True
        
        send_message(vk, peer_id, f"🎓 **УПРАВЛЕНИЕ ВСТУПИТЕЛЬНЫМИ ИСПЫТАНИЯМИ**\n\nНаправление: {direction[1]} - {direction[2]}\n\nВыберите действие:", 
                     keyboard=build_crud_keyboard())
        set_user_state(user_id, 'admin_directions_exams_menu', {'direction_id': direction_id, 'step': 'waiting_action'})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID направления) или нажмите ◀ Назад")
        return True


# ============================================================
# ОБРАБОТЧИКИ ДОБАВЛЕНИЯ/УДАЛЕНИЯ (С ПОДДЕРЖКОЙ ◀ НАЗАД)
# ============================================================

def handle_admin_directions_req_subj_add(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        direction_id = state_data.get('direction_id')
        handle_admin_directions_req_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    
    try:
        subject_id = int(text)
        direction_id = state_data.get('direction_id')
        success, msg = add_required_subject(direction_id, subject_id)
        send_message(vk, peer_id, msg)
        handle_admin_directions_req_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID предмета) или нажмите ◀ Назад")
        return True


def handle_admin_directions_req_subj_remove(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        direction_id = state_data.get('direction_id')
        handle_admin_directions_req_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    
    try:
        subject_id = int(text)
        direction_id = state_data.get('direction_id')
        success, msg = remove_required_subject(direction_id, subject_id)
        send_message(vk, peer_id, msg)
        handle_admin_directions_req_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID предмета) или нажмите ◀ Назад")
        return True


def handle_admin_directions_el_subj_add(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        direction_id = state_data.get('direction_id')
        handle_admin_directions_el_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    
    try:
        subject_id = int(text)
        direction_id = state_data.get('direction_id')
        success, msg = add_elective_subject(direction_id, subject_id)
        send_message(vk, peer_id, msg)
        handle_admin_directions_el_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID предмета) или нажмите ◀ Назад")
        return True


def handle_admin_directions_el_subj_remove(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        direction_id = state_data.get('direction_id')
        handle_admin_directions_el_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    
    try:
        subject_id = int(text)
        direction_id = state_data.get('direction_id')
        success, msg = remove_elective_subject(direction_id, subject_id)
        send_message(vk, peer_id, msg)
        handle_admin_directions_el_subj_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID предмета) или нажмите ◀ Назад")
        return True


def handle_admin_directions_exams_add(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        direction_id = state_data.get('direction_id')
        handle_admin_directions_exams_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    
    try:
        exam_id = int(text)
        direction_id = state_data.get('direction_id')
        success, msg = add_required_exam(direction_id, exam_id)
        send_message(vk, peer_id, msg)
        handle_admin_directions_exams_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID ВИ) или нажмите ◀ Назад")
        return True


def handle_admin_directions_exams_remove(vk, peer_id, user_id, text, state_data):
    if text == "◀ Назад":
        direction_id = state_data.get('direction_id')
        handle_admin_directions_exams_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    
    try:
        exam_id = int(text)
        direction_id = state_data.get('direction_id')
        success, msg = remove_required_exam(direction_id, exam_id)
        send_message(vk, peer_id, msg)
        handle_admin_directions_exams_id(vk, peer_id, user_id, str(direction_id), {})
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID ВИ) или нажмите ◀ Назад")
        return True


# ============================================================
# ПРОГРАММЫ ОБУЧЕНИЯ CRUD
# ============================================================

def show_admin_programs(vk, peer_id, user_id):
    """Показать меню управления программами"""
    send_message(vk, peer_id, "📚 **УПРАВЛЕНИЕ ПРОГРАММАМИ ОБУЧЕНИЯ**\n\nВыберите действие:", keyboard=build_crud_keyboard())
    set_user_state(user_id, 'admin_programs_menu')

def handle_admin_programs(vk, peer_id, user_id, text, state_data):
    """Обработка команд в меню программ"""
    if text == "➕ Добавить":
        # Показываем список направлений
        show_directions_list_for_programs(vk, peer_id)
        send_message(vk, peer_id, "Введите ID направления для добавления программы:\n(или нажмите ◀ Назад для возврата)")
        set_user_state(user_id, 'admin_programs_add_direction')
        return True
    
    elif text == "✏️ Редактировать":
        # Показываем список программ
        show_programs_list(vk, peer_id)
        send_message(vk, peer_id, "Введите ID программы для редактирования:\n(или нажмите ◀ Назад для возврата)")
        set_user_state(user_id, 'admin_programs_edit_id')
        return True
    
    elif text == "❌ Удалить":
        # Показываем список программ
        show_programs_list(vk, peer_id)
        send_message(vk, peer_id, "Введите ID программы для удаления:\n(или нажмите ◀ Назад для возврата)")
        set_user_state(user_id, 'admin_programs_delete')
        return True
    
    elif text == "📋 Список":
        show_programs_list(vk, peer_id)
        return True
    
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
        return True
    
    return False

def show_programs_list(vk, peer_id):
    """Показать список всех программ"""
    programs = get_all_programs_list()
    if not programs:
        send_message(vk, peer_id, "📚 Список программ пуст")
        return
    
    message = "📚 **ПРОГРАММЫ ОБУЧЕНИЯ**\n\n"
    for row in programs:
        prog_id, code, name, study_form, duration, budget, paid, fee, dir_id = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]
        
        # Преобразуем срок обучения
        years = int(duration)
        months = int(round((duration - years) * 12))
        if months == 0:
            duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'}"
        else:
            duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'} {months} {'месяц' if months == 1 else 'месяца' if months in [2,3,4] else 'месяцев'}"
        
        message += f"{prog_id}. {code} - {name}\n"
        message += f"   🎓 {study_form} | ⏱ {duration_text}\n"
        message += f"   💰 Бюджет: {budget} | Платно: {paid} | {fee:,.0f} руб/год\n\n"
        
        if len(message) > 3500:
            send_message(vk, peer_id, message)
            message = ""
    
    if message:
        send_message(vk, peer_id, message)

def handle_admin_programs_add_direction(vk, peer_id, user_id, text, state_data):
    """Обработка выбора направления для добавления программы"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        direction_id = int(text)
        direction = get_direction_by_id(direction_id)
        if not direction:
            send_message(vk, peer_id, "❌ Направление с таким ID не найдено!")
            show_directions_list_for_programs(vk, peer_id)
            send_message(vk, peer_id, "Введите ID направления для добавления программы:\n(или нажмите ◀ Назад для возврата)")
            return True
        
        set_user_state(user_id, 'admin_programs_add_form', {'direction_id': direction_id, 'direction_name': f"{direction[1]} - {direction[2]}"})
        
        message = f"📚 **ДОБАВЛЕНИЕ ПРОГРАММЫ**\n\n"
        message += f"Направление: {direction[1]} - {direction[2]}\n\n"
        message += "Выберите форму обучения:\n"
        message += "1. Очная\n2. Очно-заочная\n3. Заочная"
        
        send_message(vk, peer_id, message)
        send_message(vk, peer_id, "Введите номер формы обучения (1, 2 или 3):")
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID направления) или нажмите ◀ Назад")
        return True

def handle_admin_programs_add_form(vk, peer_id, user_id, text, state_data):
    """Обработка выбора формы обучения"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    form_map = {
        '1': 'Очная',
        '2': 'Очно-заочная',
        '3': 'Заочная'
    }
    
    if text not in form_map:
        send_message(vk, peer_id, "❌ Неверный выбор! Введите 1, 2 или 3:")
        return True
    
    study_form = form_map[text]
    
    set_user_state(user_id, 'admin_programs_add_duration', {
        'direction_id': state_data.get('direction_id'),
        'direction_name': state_data.get('direction_name'),
        'study_form': study_form
    })
    
    send_message(vk, peer_id, f"Выбрана форма: {study_form}\n\nВведите срок обучения в годах (например: 4, 4.5, 5):")
    return True

def handle_admin_programs_add_duration(vk, peer_id, user_id, text, state_data):
    """Обработка ввода срока обучения"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        duration_years = float(text.replace(',', '.'))
        if duration_years <= 0:
            send_message(vk, peer_id, "❌ Срок обучения должен быть положительным числом!")
            return True
        
        set_user_state(user_id, 'admin_programs_add_budget', {
            'direction_id': state_data.get('direction_id'),
            'direction_name': state_data.get('direction_name'),
            'study_form': state_data.get('study_form'),
            'duration_years': duration_years
        })
        
        send_message(vk, peer_id, f"Срок обучения: {duration_years} лет\n\nВведите количество БЮДЖЕТНЫХ мест:")
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (например: 4, 4.5, 5) или нажмите ◀ Назад")
        return True

def handle_admin_programs_add_budget(vk, peer_id, user_id, text, state_data):
    """Обработка ввода бюджетных мест"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        budget_places = int(text)
        if budget_places < 0:
            send_message(vk, peer_id, "❌ Количество мест не может быть отрицательным!")
            return True
        
        set_user_state(user_id, 'admin_programs_add_paid', {
            'direction_id': state_data.get('direction_id'),
            'direction_name': state_data.get('direction_name'),
            'study_form': state_data.get('study_form'),
            'duration_years': state_data.get('duration_years'),
            'budget_places': budget_places
        })
        
        send_message(vk, peer_id, f"Бюджетных мест: {budget_places}\n\nВведите количество ПЛАТНЫХ мест:")
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (количество мест) или нажмите ◀ Назад")
        return True

def handle_admin_programs_add_paid(vk, peer_id, user_id, text, state_data):
    """Обработка ввода платных мест"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        paid_places = int(text)
        if paid_places < 0:
            send_message(vk, peer_id, "❌ Количество мест не может быть отрицательным!")
            return True
        
        set_user_state(user_id, 'admin_programs_add_fee', {
            'direction_id': state_data.get('direction_id'),
            'direction_name': state_data.get('direction_name'),
            'study_form': state_data.get('study_form'),
            'duration_years': state_data.get('duration_years'),
            'budget_places': state_data.get('budget_places'),
            'paid_places': paid_places
        })
        
        send_message(vk, peer_id, f"Платных мест: {paid_places}\n\nВведите стоимость обучения в рублях за год (например: 150000):")
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (количество мест) или нажмите ◀ Назад")
        return True

def handle_admin_programs_add_fee(vk, peer_id, user_id, text, state_data):
    """Обработка ввода стоимости обучения"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        tuition_fee = int(text.replace(' ', ''))
        if tuition_fee < 0:
            send_message(vk, peer_id, "❌ Стоимость не может быть отрицательной!")
            return True
        
        direction_id = state_data.get('direction_id')
        study_form = state_data.get('study_form')
        duration_years = state_data.get('duration_years')
        budget_places = state_data.get('budget_places')
        paid_places = state_data.get('paid_places')
        
        success, msg = add_program(direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee)
        send_message(vk, peer_id, msg)
        
        show_admin_programs(vk, peer_id, user_id)
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (стоимость в рублях) или нажмите ◀ Назад")
        return True

def handle_admin_programs_edit_id(vk, peer_id, user_id, text, state_data):
    """Обработка ввода ID программы для редактирования"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        program_id = int(text)
        program = get_program_by_id(program_id)
        
        if not program:
            send_message(vk, peer_id, "❌ Программа с таким ID не найдена!")
            show_programs_list(vk, peer_id)
            send_message(vk, peer_id, "Введите ID программы для редактирования:\n(или нажмите ◀ Назад для возврата)")
            return True
        
        # Получаем список направлений
        directions = get_all_directions_for_select()
        
        set_user_state(user_id, 'admin_programs_edit_data', {'program_id': program_id})
        
        # Преобразуем срок обучения
        duration_years = program[5]
        years = int(duration_years)
        months = int(round((duration_years - years) * 12))
        if months == 0:
            duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'}"
        else:
            duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'} {months} {'месяц' if months == 1 else 'месяца' if months in [2,3,4] else 'месяцев'}"
        
        message = f"✏️ **РЕДАКТИРОВАНИЕ ПРОГРАММЫ**\n\n"
        message += f"Текущие данные:\n"
        message += f"ID: {program[0]}\n"
        message += f"Направление ID: {program[1]}\n"
        message += f"Код/Название: {program[2]} - {program[3]}\n"
        message += f"Форма обучения: {program[4]}\n"
        message += f"Срок обучения: {duration_text}\n"
        message += f"Бюджетных мест: {program[6]}\n"
        message += f"Платных мест: {program[7]}\n"
        message += f"Стоимость: {program[8]:,.0f} руб/год\n\n"
        
        message += "📋 **ДОСТУПНЫЕ НАПРАВЛЕНИЯ:**\n"
        for dir_row in directions:
            message += f"  • {dir_row[0]}. {dir_row[1]} - {dir_row[2]} ({dir_row[3]})\n"
        
        message += f"\n📝 **Введите новые данные в формате:**\n"
        message += f"ID_НАПРАВЛЕНИЯ,ФОРМА_ОБУЧЕНИЯ,СРОК_В_ГОДАХ,БЮДЖЕТ_МЕСТ,ПЛАТНЫХ_МЕСТ,СТОИМОСТЬ\n\n"
        message += f"Форма обучения: Очная, Очно-заочная или Заочная\n"
        message += f"Срок: число (например: 4, 4.5, 5)\n\n"
        message += f"**Пример:** {program[1]},Очная,4,25,15,150000"
        
        send_message(vk, peer_id, message)
        return True
        
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID программы) или нажмите ◀ Назад")
        return True

def handle_admin_programs_edit_data(vk, peer_id, user_id, text, state_data):
    """Обработка ввода новых данных для программы"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        parts = [p.strip() for p in text.split(',')]
        if len(parts) < 6:
            send_message(vk, peer_id, "❌ Неверный формат! Используйте: ID_НАПРАВЛЕНИЯ,ФОРМА_ОБУЧЕНИЯ,СРОК_В_ГОДАХ,БЮДЖЕТ_МЕСТ,ПЛАТНЫХ_МЕСТ,СТОИМОСТЬ")
            send_message(vk, peer_id, "Пример: 1,Очная,4,25,15,150000")
            return True
        
        direction_id = int(parts[0])
        study_form = parts[1]
        duration_years = float(parts[2].replace(',', '.'))
        budget_places = int(parts[3])
        paid_places = int(parts[4])
        tuition_fee = int(parts[5].replace(' ', ''))
        
        # Проверяем корректность формы обучения
        if study_form not in ['Очная', 'Очно-заочная', 'Заочная']:
            send_message(vk, peer_id, "❌ Форма обучения должна быть: Очная, Очно-заочная или Заочная")
            return True
        
        # Проверяем существование направления
        direction = get_direction_by_id(direction_id)
        if not direction:
            send_message(vk, peer_id, "❌ Направление с таким ID не найдено!")
            return True
        
        program_id = state_data.get('program_id')
        success, msg = edit_program(program_id, direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee)
        send_message(vk, peer_id, msg)
        
        show_admin_programs(vk, peer_id, user_id)
        return True
        
    except ValueError as e:
        send_message(vk, peer_id, f"❌ Ошибка в данных: {e}")
        return True
    except Exception as e:
        send_message(vk, peer_id, f"❌ Ошибка: {e}")
        return True

def handle_admin_programs_delete(vk, peer_id, user_id, text, state_data):
    """Обработка удаления программы"""
    if text == "◀ Назад":
        show_admin_programs(vk, peer_id, user_id)
        return True
    
    try:
        program_id = int(text)
        success, msg = delete_program(program_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID программы) или нажмите ◀ Назад")
    
    show_admin_programs(vk, peer_id, user_id)
    return True


# ============================================================
# FAQ CRUD С ПОДДЕРЖКОЙ КАТЕГОРИЙ
# ============================================================

def show_admin_faq(vk, peer_id, user_id):
    """Показать меню управления FAQ с выбором категории"""
    categories = get_faq_categories()
    
    # Если категорий нет, создаём стандартные
    if not categories:
        # Создаём категории по умолчанию
        from models import add_faq
        add_faq("Как подать документы?", "Для подачи документов необходимо...", "faq")
        add_faq("Какие документы нужны?", "Паспорт, аттестат, СНИЛС, фотографии", "faq")
        add_faq("Адрес", "г. Кызыл, ул. Ленина, 5", "commission")
        add_faq("Телефон", "+7 (39422) 2-18-92", "commission")
        add_faq("Режим работы", "Пн-Пт: 9:00 - 18:00\nСб: 9:00 - 13:00\nВс: выходной", "commission")
        add_faq("Сайт", "https://tuvsu.ru/abitur/", "commission")
        categories = get_faq_categories()
    
    message = "❓ **УПРАВЛЕНИЕ FAQ**\n\n"
    message += "Выберите категорию:\n"
    for cat in categories:
        cat_name = cat[0]
        if cat_name == 'faq':
            display_name = "📋 Обычные вопросы"
        elif cat_name == 'commission':
            display_name = "🏛 Приёмная комиссия"
        else:
            display_name = cat_name
        message += f"• {display_name}\n"
    
    message += "\nИли выберите действие:"
    
    send_message(vk, peer_id, message, keyboard=build_faq_admin_keyboard())
    set_user_state(user_id, 'admin_faq_category_menu')

def handle_admin_faq_category(vk, peer_id, user_id, text, state_data):
    """Обработка выбора категории FAQ"""
    category_map = {
        "📋 Обычные вопросы": "faq",
        "🏛 Приёмная комиссия": "commission"
    }
    
    if text in category_map:
        category = category_map[text]
        set_user_state(user_id, 'admin_faq_list', {'category': category})
        show_faq_by_category(vk, peer_id, user_id, category)
        return True
    
    elif text == "➕ Добавить":
        # Показываем выбор категории для добавления
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("📋 Обычные вопросы", color=VkKeyboardColor.PRIMARY)
        keyboard.add_button("🏛 Приёмная комиссия", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
        send_message(vk, peer_id, "Выберите категорию для нового вопроса:", keyboard=keyboard.get_keyboard())
        set_user_state(user_id, 'admin_faq_add_category')
        return True
    
    elif text == "◀ Назад":
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
        return True
    
    # Если текст не распознан
    send_message(vk, peer_id, "Пожалуйста, выберите категорию из кнопок выше.")
    return True

def show_faq_by_category(vk, peer_id, user_id, category):
    """Показать FAQ по категории"""
    faq_list = get_faq_by_category(category)
    
    if not faq_list:
        send_message(vk, peer_id, f"В категории '{category}' нет вопросов.")
    else:
        category_display = "Приёмная комиссия" if category == "commission" else "Обычные вопросы"
        message = f"❓ **{category_display}**\n\n"
        for row in faq_list:
            faq_id, question, answer, sort_order = row[0], row[1], row[2], row[3]
            message += f"{faq_id}. {question}\n   📝 {answer[:80]}{'...' if len(answer) > 80 else ''}\n   🔢 Порядок: {sort_order}\n\n"
            if len(message) > 3500:
                send_message(vk, peer_id, message)
                message = ""
        if message:
            send_message(vk, peer_id, message)
    
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_crud_keyboard())
    set_user_state(user_id, 'admin_faq_menu', {'category': category})

def handle_admin_faq(vk, peer_id, user_id, text, state_data):
    """Обработка команд в меню FAQ"""
    category = state_data.get('category', 'faq')
    
    if text == "➕ Добавить":
        send_message(vk, peer_id, f"Введите вопрос и ответ через запятую\nПример: Какие документы нужны?,Паспорт, аттестат, СНИЛС")
        set_user_state(user_id, 'admin_faq_add', {'category': category})
        return True
    
    elif text == "✏️ Редактировать":
        send_message(vk, peer_id, "Введите ID вопроса для редактирования:")
        set_user_state(user_id, 'admin_faq_edit_id', {'category': category})
        return True
    
    elif text == "❌ Удалить":
        send_message(vk, peer_id, "Введите ID вопроса для удаления:")
        set_user_state(user_id, 'admin_faq_delete', {'category': category})
        return True
    
    elif text == "📋 Список":
        show_faq_by_category(vk, peer_id, user_id, category)
        return True
    
    elif text == "◀ Назад":
        show_admin_faq(vk, peer_id, user_id)
        return True
    
    return False

def handle_admin_faq_add_category(vk, peer_id, user_id, text, state_data):
    """Обработка выбора категории для добавления вопроса"""
    category_map = {
        "📋 Обычные вопросы": "faq",
        "🏛 Приёмная комиссия": "commission"
    }
    
    if text in category_map:
        category = category_map[text]
        send_message(vk, peer_id, f"Введите вопрос и ответ через запятую для категории '{text}'\nПример: Какие документы нужны?,Паспорт, аттестат, СНИЛС")
        set_user_state(user_id, 'admin_faq_add', {'category': category})
        return True
    elif text == "◀ Назад":
        show_admin_faq(vk, peer_id, user_id)
        return True
    else:
        send_message(vk, peer_id, "Пожалуйста, выберите категорию из кнопок выше.")
        return True

def handle_admin_faq_add(vk, peer_id, user_id, text, state_data):
    category = state_data.get('category', 'faq')
    try:
        parts = text.split(',', 1)
        question = parts[0].strip()
        answer = parts[1].strip() if len(parts) > 1 else ""
        success, msg = add_faq(question, answer, category)
        send_message(vk, peer_id, msg)
    except Exception as e:
        send_message(vk, peer_id, f"Ошибка: {e}")
    show_faq_by_category(vk, peer_id, user_id, category)
    return True

def handle_admin_faq_edit_id(vk, peer_id, user_id, text, state_data):
    category = state_data.get('category', 'faq')
    if text == "◀ Назад":
        show_faq_by_category(vk, peer_id, user_id, category)
        return True
    
    try:
        faq_id = int(text)
        # Проверяем, существует ли вопрос
        faq = db.fetch_one("SELECT id, question, answer FROM faq WHERE id = ?", (faq_id,))
        if not faq:
            send_message(vk, peer_id, "❌ Вопрос с таким ID не найден!")
            show_faq_by_category(vk, peer_id, user_id, category)
            return True
        
        set_user_state(user_id, 'admin_faq_edit_data', {'id': faq_id, 'category': category})
        send_message(vk, peer_id, f"Введите новый вопрос и ответ для FAQ ID {faq_id} через запятую\nПример: Новый вопрос,Новый ответ")
        return True
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID вопроса) или нажмите ◀ Назад")
        return True

def handle_admin_faq_edit_data(vk, peer_id, user_id, text, state_data):
    faq_id = state_data.get('id')
    category = state_data.get('category', 'faq')
    try:
        parts = text.split(',', 1)
        question = parts[0].strip()
        answer = parts[1].strip() if len(parts) > 1 else ""
        success, msg = edit_faq(faq_id, question, answer)
        send_message(vk, peer_id, msg)
    except Exception as e:
        send_message(vk, peer_id, f"Ошибка: {e}")
    show_faq_by_category(vk, peer_id, user_id, category)
    return True

def handle_admin_faq_delete(vk, peer_id, user_id, text, state_data):
    category = state_data.get('category', 'faq')
    if text == "◀ Назад":
        show_faq_by_category(vk, peer_id, user_id, category)
        return True
    
    try:
        faq_id = int(text)
        success, msg = delete_faq(faq_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID вопроса) или нажмите ◀ Назад")
    show_faq_by_category(vk, peer_id, user_id, category)
    return True


# ============================================================
# ОТЛОЖЕННАЯ РАССЫЛКА
# ============================================================

from scheduler import (
    add_scheduled_broadcast, list_scheduled_broadcasts,
    cancel_scheduled_broadcast
)


def show_scheduled_broadcasts(vk, peer_id):
    """Показать список запланированных рассылок"""
    result = list_scheduled_broadcasts()
    send_message(vk, peer_id, result)


def handle_admin_scheduled_broadcast(vk, peer_id, user_id, text, state_data):
    """Обработка создания отложенной рассылки"""
    
    if 'step' not in state_data:
        send_message(vk, peer_id, 
            "📅 Введите дату и время рассылки в формате:\n"
            "ГГГГ-ММ-ДД ЧЧ:ММ:СС\n\n"
            "Пример: 2026-05-25 15:30:00")
        set_user_state(user_id, 'admin_scheduled_broadcast', {'step': 'datetime'})
        return True
    
    elif state_data.get('step') == 'datetime':
        scheduled_time = text
        set_user_state(user_id, 'admin_scheduled_broadcast', {
            'step': 'messages',
            'scheduled_time': scheduled_time,
            'messages': []
        })
        send_message(vk, peer_id,
            "✏️ Теперь создайте сообщения для рассылки.\n\n"
            "📝 **Отправить текст** → напишите текст и нажмите Enter\n"
            "📷 **Отправить фото** → просто отправьте фото\n"
            "📷+📝 **Отправить фото с текстом** → отправьте фото, затем в следующем сообщении отправьте текст\n\n"
            "После добавления всех сообщений нажмите '✅ Завершить'")
        send_message(vk, peer_id, "Выберите действие:", keyboard=build_scheduled_compose_keyboard())
        return True
    
    elif state_data.get('step') == 'messages':
        messages = state_data.get('messages', [])
        
        if text == '✅ Завершить' or text == '/done':
            if not messages:
                send_message(vk, peer_id, "❌ Не добавлено ни одного сообщения!")
                return True
            
            scheduled_time = state_data.get('scheduled_time')
            success, msg = add_scheduled_broadcast(user_id, messages, scheduled_time)
            send_message(vk, peer_id, msg)
            send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", 
                         keyboard=build_admin_menu_keyboard())
            set_user_state(user_id, 'admin_menu')
            return True
        
        elif text == '➕ Добавить ещё':
            set_user_state(user_id, 'admin_scheduled_wait_content', {
                'scheduled_time': state_data.get('scheduled_time'),
                'messages': messages
            })
            send_message(vk, peer_id, "✏️ Отправьте текст или фото для следующего сообщения:")
            return True
        
        elif text == '❌ Отменить':
            send_message(vk, peer_id, "❌ Создание рассылки отменено.")
            send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", 
                         keyboard=build_admin_menu_keyboard())
            set_user_state(user_id, 'admin_menu')
            return True
        
        else:
            if not text or text.strip() == '':
                send_message(vk, peer_id, "❌ Текст не может быть пустым! Введите текст:")
                return True
            
            if text in ['✅ Завершить', '/done', '➕ Добавить ещё', '❌ Отменить']:
                send_message(vk, peer_id, "❌ Используйте кнопки для управления!")
                return True
            
            messages.append((text, None))
            set_user_state(user_id, 'admin_scheduled_broadcast', {
                'step': 'messages',
                'scheduled_time': state_data.get('scheduled_time'),
                'messages': messages
            })
            send_message(vk, peer_id, f"✅ Сообщение {len(messages)} добавлено!\n\n"
                         f"📝 Текст: {text[:50]}...\n"
                         f"📷 Фото: нет\n\n"
                         f"Можно добавить ещё или нажать '✅ Завершить'")
            send_message(vk, peer_id, "Выберите действие:", keyboard=build_scheduled_compose_keyboard())
            return True


def handle_admin_scheduled_photo(vk, peer_id, user_id, msg, state_data):
    """Обработка фото для отложенной рассылки"""
    
    text = msg.get('text', '').strip() if msg.get('text') else ''
    
    photo_attachment = None
    if msg.get('attachments'):
        for attach in msg['attachments']:
            if attach['type'] == 'photo':
                photo = attach['photo']
                max_size = 0
                best_photo = None
                for size in photo['sizes']:
                    if size['width'] * size['height'] > max_size:
                        max_size = size['width'] * size['height']
                        best_photo = size
                
                if best_photo:
                    photo_url = best_photo['url']
                    temp_path = f"temp_photo_{user_id}_{int(time.time())}.jpg"
                    if download_photo_by_url(photo_url, temp_path):
                        uploaded = upload_photo_to_messages(vk, temp_path, peer_id)
                        if uploaded:
                            photo_attachment = uploaded
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                break
    
    if not photo_attachment:
        send_message(vk, peer_id, "❌ Не удалось загрузить фото. Попробуйте ещё раз.")
        return True
    
    messages = state_data.get('messages', [])
    scheduled_time = state_data.get('scheduled_time')
    
    if text and text != '':
        messages.append((text, photo_attachment))
        send_message(vk, peer_id, f"✅ Сообщение {len(messages)} добавлено!\n\n"
                     f"📝 Текст: {text[:50]}...\n"
                     f"📷 Фото: есть (с текстом)\n\n")
    else:
        messages.append(("", photo_attachment))
        send_message(vk, peer_id, f"✅ Сообщение {len(messages)} добавлено!\n\n"
                     f"📝 Текст: (только фото)\n"
                     f"📷 Фото: есть\n\n")
    
    set_user_state(user_id, 'admin_scheduled_broadcast', {
        'step': 'messages',
        'scheduled_time': scheduled_time,
        'messages': messages
    })
    
    send_message(vk, peer_id, "Можно добавить ещё или нажать '✅ Завершить'")
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_scheduled_compose_keyboard())
    
    return True


def handle_admin_scheduled_wait_content(vk, peer_id, user_id, text, msg, state_data):
    """Ожидание содержимого (текста или фото) для следующего сообщения"""
    
    if text == '❌ Отменить':
        send_message(vk, peer_id, "❌ Создание рассылки отменено.")
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", 
                     keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
        return True
    
    photo_attachment = None
    if msg.get('attachments'):
        for attach in msg['attachments']:
            if attach['type'] == 'photo':
                photo = attach['photo']
                max_size = 0
                best_photo = None
                for size in photo['sizes']:
                    if size['width'] * size['height'] > max_size:
                        max_size = size['width'] * size['height']
                        best_photo = size
                
                if best_photo:
                    photo_url = best_photo['url']
                    temp_path = f"temp_photo_{user_id}_{int(time.time())}.jpg"
                    if download_photo_by_url(photo_url, temp_path):
                        uploaded = upload_photo_to_messages(vk, temp_path, peer_id)
                        if uploaded:
                            photo_attachment = uploaded
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                break
    
    if photo_attachment:
        set_user_state(user_id, 'admin_scheduled_wait_text', {
            'scheduled_time': state_data.get('scheduled_time'),
            'messages': state_data.get('messages', []),
            'temp_photo': photo_attachment
        })
        send_message(vk, peer_id, "✅ Фото получено!\n\nВведите текст для этого фото\n(или отправьте '.' если фото без текста):")
    else:
        if not text or text.strip() == '':
            send_message(vk, peer_id, "❌ Текст не может быть пустым! Отправьте текст или фото:")
            return True
        
        messages = state_data.get('messages', [])
        scheduled_time = state_data.get('scheduled_time')
        
        messages.append((text, None))
        
        set_user_state(user_id, 'admin_scheduled_broadcast', {
            'step': 'messages',
            'scheduled_time': scheduled_time,
            'messages': messages
        })
        
        send_message(vk, peer_id, f"✅ Сообщение {len(messages)} добавлено!\n\n"
                     f"📝 Текст: {text[:50]}...\n"
                     f"📷 Фото: нет\n\n")
        send_message(vk, peer_id, "Выберите действие:", keyboard=build_scheduled_compose_keyboard())
    
    return True


def handle_admin_scheduled_wait_text(vk, peer_id, user_id, text, msg, state_data):
    """Ожидание текста для сообщения с фото"""
    
    if text == '❌ Отменить':
        send_message(vk, peer_id, "❌ Создание рассылки отменено.")
        send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", 
                     keyboard=build_admin_menu_keyboard())
        set_user_state(user_id, 'admin_menu')
        return True
    
    messages = state_data.get('messages', [])
    scheduled_time = state_data.get('scheduled_time')
    photo = state_data.get('temp_photo')
    
    if text == '.':
        messages.append(("", photo))
        result_text = "(только фото)"
    else:
        if not text or text.strip() == '':
            send_message(vk, peer_id, "❌ Текст не может быть пустым! Введите текст (или отправьте '.' для фото без текста):")
            return True
        messages.append((text, photo))
        result_text = text[:50] + "..."
    
    set_user_state(user_id, 'admin_scheduled_broadcast', {
        'step': 'messages',
        'scheduled_time': scheduled_time,
        'messages': messages
    })
    
    send_message(vk, peer_id, f"✅ Сообщение {len(messages)} добавлено!\n\n"
                 f"📝 Текст: {result_text}\n"
                 f"📷 Фото: есть\n\n")
    send_message(vk, peer_id, "Выберите действие:", keyboard=build_scheduled_compose_keyboard())
    
    return True


def handle_cancel_scheduled(vk, peer_id, user_id, text, state_data):
    """Отмена запланированной рассылки по ID"""
    try:
        broadcast_id = int(text)
        success, msg = cancel_scheduled_broadcast(broadcast_id)
        send_message(vk, peer_id, msg)
    except ValueError:
        send_message(vk, peer_id, "❌ Введите число (ID рассылки)")
    
    send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", 
                 keyboard=build_admin_menu_keyboard())
    set_user_state(user_id, 'admin_menu')
    return True


# ============================================================
# СТАТИСТИКА И ИСТОРИЯ РАССЫЛОК
# ============================================================

def show_broadcast_stats(vk, peer_id):
    """Показать статистику рассылки"""
    from user_states import get_users_count, get_broadcast_recipients
    from db import db
    
    users_count = get_users_count()
    subscribed_count = len(get_broadcast_recipients())
    unsubscribed_count = db.fetch_one('SELECT COUNT(*) FROM broadcast_blacklist')[0]
    
    message = (
        "📊 **СТАТИСТИКА РАССЫЛКИ**\n\n"
        f"👥 Всего пользователей: {users_count}\n"
        f"✅ Подписаны на рассылку: {subscribed_count}\n"
        f"❌ Отписались: {unsubscribed_count}\n\n"
        "ℹ️ Отписаться можно командой /stop_broadcast\n"
        "Подписаться заново: /start_broadcast"
    )
    send_message(vk, peer_id, message)


def show_broadcast_history(vk, peer_id):
    """Показать историю рассылок"""
    from user_states import get_broadcast_history
    
    history = get_broadcast_history(10)
    if not history:
        send_message(vk, peer_id, "📋 История рассылок пуста.")
        return
    
    message = "📋 **ИСТОРИЯ РАССЫЛОК (последние 10)**\n\n"
    for row in history:
        hist_id, admin_id, msg, photo, recipients, sent_at = row[0], row[1], row[2], row[3], row[4], row[5]
        sent_at_formatted = sent_at[:16] if sent_at else "неизвестно"
        msg_preview = msg[:50] + "..." if len(msg) > 50 else msg
        has_photo = "📷 с фото" if photo else "📝 без фото"
        message += f"• {sent_at_formatted} | Админ: {admin_id} {has_photo}\n  Получателей: {recipients}\n  Текст: {msg_preview}\n\n"
        if len(message) > 3500:
            send_message(vk, peer_id, message)
            message = ""
    if message:
        send_message(vk, peer_id, message)


def download_photo_by_url(url, save_path):
    """Скачать фото по URL"""
    import requests
    import os
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                print(f"URL не ведёт на изображение: {content_type}")
                return False
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            if os.path.getsize(save_path) == 0:
                print(f"Скачанный файл пуст: {save_path}")
                return False
            return True
        else:
            print(f"Ошибка скачивания фото: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Ошибка скачивания фото: {e}")
        return False


def upload_photo_to_messages(vk, photo_path, peer_id):
    """Загрузить фото для отправки в сообщения"""
    import os
    from vk_api.upload import VkUpload
    
    if not os.path.exists(photo_path):
        print(f"Файл не найден: {photo_path}")
        return None
    
    if os.path.getsize(photo_path) == 0:
        print(f"Файл пустой: {photo_path}")
        return None
    
    try:
        upload = VkUpload(vk)
        photo = upload.photo_messages(photos=photo_path, peer_id=peer_id)
        
        if photo and len(photo) > 0:
            owner_id = photo[0].get('owner_id')
            photo_id = photo[0].get('id')
            if owner_id and photo_id:
                return f"photo{owner_id}_{photo_id}"
        print(f"Неверный формат ответа: {photo}")
        return None
    except Exception as e:
        print(f"Ошибка загрузки фото: {e}")
        return None
