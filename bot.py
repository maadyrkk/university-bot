import os
import time
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from config import get_admin_ids, get_vk_config
from db import db
from user_states import (
    get_user_state, set_user_state, clear_user_state, 
    remove_from_blacklist, add_to_blacklist, is_user_blacklisted,
    get_all_users
)
from keyboards import (
    build_main_menu_keyboard, build_admin_menu_keyboard, 
    build_broadcast_keyboard, build_levels_keyboard, build_faq_keyboard,
    build_scheduled_menu_keyboard, build_scheduled_compose_keyboard
)
from admin_handlers import (
    show_admin_stats, show_admin_levels, show_admin_faculties, show_admin_subjects,
    show_admin_entrance_exams, show_admin_directions, show_admin_programs, show_admin_faq,
    handle_admin_levels, handle_admin_levels_add, handle_admin_levels_edit_id,
    handle_admin_levels_edit_name, handle_admin_levels_delete,
    handle_admin_faculties, handle_admin_faculties_add, handle_admin_faculties_edit_id,
    handle_admin_faculties_edit_name, handle_admin_faculties_delete,
    handle_admin_subjects, handle_admin_subjects_add, handle_admin_subjects_edit_id,
    handle_admin_subjects_edit_data, handle_admin_subjects_delete,
    handle_admin_exams, handle_admin_exams_add, handle_admin_exams_edit_id,
    handle_admin_exams_edit_data, handle_admin_exams_delete,
    handle_admin_faq, handle_admin_faq_add, handle_admin_faq_edit_id,
    handle_admin_faq_edit_data, handle_admin_faq_delete,
    handle_admin_directions, handle_admin_directions_add_faculty,
    handle_admin_directions_add_level, handle_admin_directions_add_code,
    handle_admin_directions_add_name, handle_admin_directions_add_desc,
    handle_admin_directions_edit_id, handle_admin_directions_edit_data,
    handle_admin_directions_delete,
    show_scheduled_broadcasts,
    handle_admin_scheduled_broadcast,
    handle_admin_scheduled_photo,
    handle_admin_scheduled_wait_content,
    handle_admin_scheduled_wait_text,
    show_broadcast_stats,
    show_broadcast_history,
    handle_cancel_scheduled,
    handle_admin_directions_required_subjects,
    handle_admin_directions_elective_subjects,
    handle_admin_directions_exams,
    handle_admin_directions_req_subj_id,
    handle_admin_directions_req_subj_add,
    handle_admin_directions_req_subj_remove,
    handle_admin_directions_el_subj_id,
    handle_admin_directions_el_subj_add,
    handle_admin_directions_el_subj_remove,
    handle_admin_directions_exams_id,
    handle_admin_directions_exams_add,
    handle_admin_directions_exams_remove,
    show_admin_programs,
    handle_admin_programs,
    handle_admin_programs_add_direction,
    handle_admin_programs_add_form,
    handle_admin_programs_add_duration,
    handle_admin_programs_add_budget,
    handle_admin_programs_add_paid,
    handle_admin_programs_add_fee,
    handle_admin_programs_edit_id,
    handle_admin_programs_edit_data,
    handle_admin_programs_delete,
    show_admin_faq,
    handle_admin_faq_category,
    handle_admin_faq,
    handle_admin_faq_add_category,
    handle_admin_faq_add,
    handle_admin_faq_edit_id,
    handle_admin_faq_edit_data,
    handle_admin_faq_delete
)
from user_handlers import handle_user_message
from utils import send_message, send_message_with_links
from scheduler import init_scheduler_db, start_scheduler_thread


# Константы для главного меню
MAIN_MENU_BUTTONS = ["Уровни образования", "Поиск", "О приёмной комиссии", "Часто задаваемые вопросы"]
MENU_BACK_BUTTONS = ["🏠 Меню", "🏠 меню", "Главное меню"]
ALL_MENU_BUTTONS = MAIN_MENU_BUTTONS + MENU_BACK_BUTTONS


def run_bot():
    config = get_vk_config()
    VK_GROUP_TOKEN = config['token']
    VK_GROUP_ID = config['group_id']
    ADMIN_IDS = get_admin_ids()
    
    if not VK_GROUP_TOKEN or not VK_GROUP_ID:
        print("Ошибка: не заданы VK_GROUP_TOKEN или VK_GROUP_ID в .env файле")
        return
    
    vk_session = VkApi(token=VK_GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

    start_scheduler_thread(vk)
    
    print("Бот запущен и ожидает сообщения...")
    print(f"Администраторы: {ADMIN_IDS}")
    
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message
            peer_id = msg['peer_id']
            user_id = msg['from_id']
            text = msg['text'].strip() if msg['text'] else ''
            
            print(f"{user_id}: {text}")
            
            # ========== КОМАНДА /start ==========
            if text.lower() in ['/start', 'начать']:
                clear_user_state(user_id)
                remove_from_blacklist(user_id)
                send_message(vk, peer_id, "Здравствуйте! Я чат-бот приёмной комиссии Тувинского государственного университета.\n\nВыберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                set_user_state(user_id, 'main_menu')
                continue
            
            # ========== КОМАНДА /admin ==========
            if user_id in ADMIN_IDS and text == '/admin':
                clear_user_state(user_id)
                send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
                set_user_state(user_id, 'admin_menu')
                continue
            
            # ========== КОМАНДЫ ПОДПИСКИ/ОТПИСКИ ==========
            if text.lower() == '/stop_broadcast' or text.lower() == 'стоп рассылка':
                if add_to_blacklist(user_id):
                    send_message(vk, peer_id, "❌ Вы отписались от рассылки уведомлений.")
                else:
                    send_message(vk, peer_id, "❌ Произошла ошибка.")
                continue
            
            if text.lower() == '/start_broadcast' or text.lower() == 'начать рассылку':
                if remove_from_blacklist(user_id):
                    send_message(vk, peer_id, "✅ Вы подписались на рассылку уведомлений!")
                else:
                    send_message(vk, peer_id, "✅ Вы уже подписаны на рассылку!")
                continue

            # ========== ГЛАВНОЕ МЕНЮ ==========
            if text in MAIN_MENU_BUTTONS:
                clear_user_state(user_id)
                
                if text == "Уровни образования":
                    send_message(vk, peer_id, "Выберите уровень образования:", keyboard=build_levels_keyboard())
                    set_user_state(user_id, 'selecting_level')
                elif text == "Поиск":
                    send_message(vk, peer_id, "Введите код специальности:")
                    set_user_state(user_id, 'searching')
                elif text == "Часто задаваемые вопросы":
                    from models import get_all_faq
                    faq_list = get_all_faq()
                    if not faq_list:
                        send_message(vk, peer_id, "Раздел FAQ пока пуст.")
                        set_user_state(user_id, 'main_menu')
                    else:
                        send_message(vk, peer_id, "❓ Часто задаваемые вопросы:\n\nВыберите интересующий вас вопрос:", keyboard=build_faq_keyboard())
                        set_user_state(user_id, 'selecting_faq')
                elif text == "О приёмной комиссии":
                    from models import get_commission_text, get_commission_info
                    from utils import send_message_with_links
                    
                    message = get_commission_text()
                    
                    # Проверяем, есть ли ссылка на сайт
                    info = get_commission_info()
                    has_site = False
                    site_url = None
                    
                    for row in info:
                        if "Сайт" in row[1]:  # question содержит "Сайт"
                            has_site = True
                            site_url = row[2]  # answer
                            break
                    
                    if has_site and site_url:
                        send_message_with_links(vk, peer_id, message, "Официальный сайт ТувГУ", site_url)
                    else:
                        send_message(vk, peer_id, message)
                    
                    send_message(vk, peer_id, "Выберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                    set_user_state(user_id, 'main_menu')
                    continue
                continue
            
            # ========== ПРОВЕРКА СУЩЕСТВОВАНИЯ ПОЛЬЗОВАТЕЛЯ ==========
            user_exists = db.fetch_one("SELECT 1 FROM user_states WHERE user_id = ?", (user_id,))
            
            if not user_exists:
                remove_from_blacklist(user_id)
                set_user_state(user_id, 'main_menu')
                send_message(vk, peer_id, "Здравствуйте! Я чат-бот приёмной комиссии Тувинского государственного университета.\n\nВыберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                continue
            
            if is_user_blacklisted(user_id):
                remove_from_blacklist(user_id)
            
            # ========== КНОПКА "МЕНЮ" ==========
            if text in MENU_BACK_BUTTONS:
                clear_user_state(user_id)
                send_message(vk, peer_id, "Выберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                set_user_state(user_id, 'main_menu')
                continue
            

            

            
            # ========== ПОЛУЧАЕМ ТЕКУЩЕЕ СОСТОЯНИЕ ==========
            user_state = get_user_state(user_id)
            current_state = user_state['state']
            state_data = user_state['data']
            
            # ========== АДМИН-ПАНЕЛЬ ==========
            if current_state == 'admin_menu':
                if text == "📊 Статистика":
                    show_admin_stats(vk, peer_id)
                elif text == "📚 Уровни образования":
                    show_admin_levels(vk, peer_id, user_id)
                elif text == "🏛 Факультеты":
                    show_admin_faculties(vk, peer_id, user_id)
                elif text == "📖 Предметы ЕГЭ":
                    show_admin_subjects(vk, peer_id, user_id)
                elif text == "🎓 ВИ (вступительные)":
                    show_admin_entrance_exams(vk, peer_id, user_id)
                elif text == "📋 Направления":
                    show_admin_directions(vk, peer_id, user_id)
                elif text == "📚 Программы":
                    show_admin_programs(vk, peer_id, user_id)
                elif text == "Часто задаваемые вопросы (ред.)":
                    show_admin_faq(vk, peer_id, user_id)
                elif text == "📢 Рассылка":
                    send_message(vk, peer_id, "📢 **РАССЫЛКА**\n\nВыберите действие:", keyboard=build_broadcast_keyboard())
                    set_user_state(user_id, 'admin_broadcast_menu')
                continue
            
            # ========== МЕНЮ РАССЫЛКИ ==========
            if current_state == 'admin_broadcast_menu':
                if text == "📊 Статистика рассылки":
                    show_broadcast_stats(vk, peer_id)
                elif text == "⏰ Отложенная рассылка":
                    send_message(vk, peer_id, "⏰ **ОТЛОЖЕННАЯ РАССЫЛКА**\n\n"
                                "Вы можете запланировать рассылку на определённое время.\n\n"
                                "Доступные действия:", keyboard=build_scheduled_menu_keyboard())
                    set_user_state(user_id, 'admin_scheduled_menu')
                elif text == "📋 Список пользователей":
                    users = get_all_users()
                    if not users:
                        send_message(vk, peer_id, "Список пользователей пуст.")
                    else:
                        message = "👥 **СПИСОК ПОЛЬЗОВАТЕЛЕЙ**\n\n"
                        for i, row in enumerate(users, 1):
                            user_id_val = row[0]
                            is_subscribed = "✅" if not is_user_blacklisted(user_id_val) else "❌"
                            message += f"{i}. {is_subscribed} {user_id_val}\n"
                            if len(message) > 3500:
                                send_message(vk, peer_id, message)
                                message = ""
                        if message:
                            send_message(vk, peer_id, message)
                elif text == "📜 История рассылок":
                    show_broadcast_history(vk, peer_id)
                elif text == "◀ Назад":
                    send_message(vk, peer_id, "🔐 **АДМИН-ПАНЕЛЬ**\n\nВыберите действие:", keyboard=build_admin_menu_keyboard())
                    set_user_state(user_id, 'admin_menu')
                continue

            # ========== МЕНЮ ОТЛОЖЕННОЙ РАССЫЛКИ ==========
            if current_state == 'admin_scheduled_menu':
                if text == "📅 Создать отложенную":
                    # Переходим в состояние ожидания даты
                    set_user_state(user_id, 'admin_scheduled_broadcast', {'step': 'datetime'})
                    send_message(vk, peer_id, 
                        "📅 Введите дату и время рассылки в формате:\n"
                        "ГГГГ-ММ-ДД ЧЧ:ММ:СС\n\n"
                        "Пример: 2026-05-25 15:30:00")
                    continue
                elif text == "📋 Список запланированных":
                    show_scheduled_broadcasts(vk, peer_id)
                elif text == "❌ Отменить рассылку":
                    send_message(vk, peer_id, "❌ Введите ID рассылки для отмены:")
                    set_user_state(user_id, 'admin_scheduled_cancel')
                elif text == "◀ Назад":
                    send_message(vk, peer_id, "📢 **РАССЫЛКА**\n\nВыберите действие:", keyboard=build_broadcast_keyboard())
                    set_user_state(user_id, 'admin_broadcast_menu')
                continue



            # ========== СОЗДАНИЕ ОТЛОЖЕННОЙ РАССЫЛКИ (С ПРОВЕРКОЙ ФОТО) ==========
            if current_state == 'admin_scheduled_broadcast':
                # Проверяем наличие фото
                has_photo = False
                if msg.get('attachments'):
                    for attach in msg['attachments']:
                        if attach['type'] == 'photo':
                            has_photo = True
                            handled = handle_admin_scheduled_photo(vk, peer_id, user_id, msg, state_data)
                            if handled:
                                break
                    if has_photo:
                        continue
                # Если фото нет, обрабатываем как текст
                handled = handle_admin_scheduled_broadcast(vk, peer_id, user_id, text, state_data)
                if handled:
                    continue

            # ========== ОЖИДАНИЕ ID ДЛЯ ОТМЕНЫ ==========
            if current_state == 'admin_scheduled_cancel':
                handled = handle_cancel_scheduled(vk, peer_id, user_id, text, state_data)
                if handled:
                    continue

            # ========== ОЖИДАНИЕ СОДЕРЖИМОГО ==========
            if current_state == 'admin_scheduled_wait_content':
                handled = handle_admin_scheduled_wait_content(vk, peer_id, user_id, text, msg, state_data)
                if handled:
                    continue

            # ========== ОЖИДАНИЕ ТЕКСТА ДЛЯ ФОТО ==========
            if current_state == 'admin_scheduled_wait_text':
                handled = handle_admin_scheduled_wait_text(vk, peer_id, user_id, text, msg, state_data)
                if handled:
                    continue
            
            
            
            # ========== CRUD ДЛЯ УРОВНЕЙ ОБРАЗОВАНИЯ ==========
            if current_state == 'admin_levels_menu':
                if handle_admin_levels(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_levels_add':
                if handle_admin_levels_add(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_levels_edit_id':
                if handle_admin_levels_edit_id(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_levels_edit_name':
                if handle_admin_levels_edit_name(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_levels_delete':
                if handle_admin_levels_delete(vk, peer_id, user_id, text):
                    continue
            
            # ========== CRUD ДЛЯ ФАКУЛЬТЕТОВ ==========
            if current_state == 'admin_faculties_menu':
                if handle_admin_faculties(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_faculties_add':
                if handle_admin_faculties_add(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_faculties_edit_id':
                if handle_admin_faculties_edit_id(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_faculties_edit_name':
                if handle_admin_faculties_edit_name(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_faculties_delete':
                if handle_admin_faculties_delete(vk, peer_id, user_id, text):
                    continue
            
            # ========== CRUD ДЛЯ ПРЕДМЕТОВ ЕГЭ ==========
            if current_state == 'admin_subjects_menu':
                if handle_admin_subjects(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_subjects_add':
                if handle_admin_subjects_add(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_subjects_edit_id':
                if handle_admin_subjects_edit_id(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_subjects_edit_data':
                if handle_admin_subjects_edit_data(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_subjects_delete':
                if handle_admin_subjects_delete(vk, peer_id, user_id, text):
                    continue
            
            # ========== CRUD ДЛЯ ВСТУПИТЕЛЬНЫХ ИСПЫТАНИЙ ==========
            if current_state == 'admin_exams_menu':
                if handle_admin_exams(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_exams_add':
                if handle_admin_exams_add(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_exams_edit_id':
                if handle_admin_exams_edit_id(vk, peer_id, user_id, text):
                    continue
            if current_state == 'admin_exams_edit_data':
                if handle_admin_exams_edit_data(vk, peer_id, user_id, text, state_data):
                    continue
            if current_state == 'admin_exams_delete':
                if handle_admin_exams_delete(vk, peer_id, user_id, text):
                    continue
            
            # ========== CRUD ДЛЯ FAQ ==========
            if current_state == 'admin_faq_category_menu':
                if handle_admin_faq_category(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_list':
                if handle_admin_faq(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_menu':
                if handle_admin_faq(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_add_category':
                if handle_admin_faq_add_category(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_add':
                if handle_admin_faq_add(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_edit_id':
                if handle_admin_faq_edit_id(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_edit_data':
                if handle_admin_faq_edit_data(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_faq_delete':
                if handle_admin_faq_delete(vk, peer_id, user_id, text, state_data):
                    continue

            # ========== CRUD ДЛЯ НАПРАВЛЕНИЙ ==========
            if current_state == 'admin_directions_menu':
                if handle_admin_directions(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_add_faculty':
                if handle_admin_directions_add_faculty(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_add_level':
                if handle_admin_directions_add_level(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_add_code':
                if handle_admin_directions_add_code(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_add_name':
                if handle_admin_directions_add_name(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_add_desc':
                if handle_admin_directions_add_desc(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_edit_id':
                if handle_admin_directions_edit_id(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_edit_data':
                if handle_admin_directions_edit_data(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_delete':
                if handle_admin_directions_delete(vk, peer_id, user_id, text, state_data):
                    continue
            
            if current_state == 'admin_directions_req_subj_id':
                if handle_admin_directions_req_subj_id(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_req_subj_menu':
                if handle_admin_directions_required_subjects(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_req_subj_add':
                if handle_admin_directions_req_subj_add(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_req_subj_remove':
                if handle_admin_directions_req_subj_remove(vk, peer_id, user_id, text, state_data):
                    continue

            # Предметы на выбор
            if current_state == 'admin_directions_el_subj_id':
                if handle_admin_directions_el_subj_id(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_el_subj_menu':
                if handle_admin_directions_elective_subjects(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_el_subj_add':
                if handle_admin_directions_el_subj_add(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_el_subj_remove':
                if handle_admin_directions_el_subj_remove(vk, peer_id, user_id, text, state_data):
                    continue

            # ВИ
            if current_state == 'admin_directions_exams_id':
                if handle_admin_directions_exams_id(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_exams_menu':
                if handle_admin_directions_exams(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_exams_add':
                if handle_admin_directions_exams_add(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_directions_exams_remove':
                if handle_admin_directions_exams_remove(vk, peer_id, user_id, text, state_data):
                    continue

            # ========== CRUD ДЛЯ ПРОГРАММ ==========
            if current_state == 'admin_programs_menu':
                if handle_admin_programs(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_add_direction':
                if handle_admin_programs_add_direction(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_add_form':
                if handle_admin_programs_add_form(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_add_duration':
                if handle_admin_programs_add_duration(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_add_budget':
                if handle_admin_programs_add_budget(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_add_paid':
                if handle_admin_programs_add_paid(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_add_fee':
                if handle_admin_programs_add_fee(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_edit_id':
                if handle_admin_programs_edit_id(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_edit_data':
                if handle_admin_programs_edit_data(vk, peer_id, user_id, text, state_data):
                    continue

            if current_state == 'admin_programs_delete':
                if handle_admin_programs_delete(vk, peer_id, user_id, text, state_data):
                    continue
                
            
            # ========== ПОЛЬЗОВАТЕЛЬСКИЕ СЦЕНАРИИ ==========
            handled = handle_user_message(vk, user_id, peer_id, text, current_state, state_data)
            if handled:
                continue

            # ========== КНОПКА "НАЗАД" ==========
            if text == "◀ Назад":
                clear_user_state(user_id)
                send_message(vk, peer_id, "Выберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                set_user_state(user_id, 'main_menu')
                continue
            
            # ========== ЕСЛИ СОСТОЯНИЕ None ИЛИ main_menu ==========
            if current_state is None or current_state == 'main_menu':
                send_message(vk, peer_id, "Выберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                set_user_state(user_id, 'main_menu')
                continue
            
            # ========== НЕИЗВЕСТНАЯ КОМАНДА ==========
            send_message(vk, peer_id, "Пожалуйста, воспользуйтесь кнопками меню.\nЕсли меню не отображается, напишите «Начать» или /start", keyboard=build_main_menu_keyboard())
            set_user_state(user_id, 'main_menu')


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == '__main__':
    print("Запуск чат-бота")
    
    while True:
        try:
            run_bot()
        except KeyboardInterrupt:
            print("\nБот остановлен пользователем")
            break
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            print("Перезапуск через 5 секунд...")
            time.sleep(5)
    
    print("Работа бота завершена")
