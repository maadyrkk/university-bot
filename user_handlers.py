from models import (
    get_education_levels, get_faculties_by_level, get_directions_by_faculty_and_level,
    get_direction_with_forms, get_specialty_details, get_all_faq, search_directions
)
from user_states import set_user_state, clear_user_state
from keyboards import build_levels_keyboard, build_faculties_keyboard, build_study_form_keyboard, build_faq_keyboard, build_main_menu_keyboard
from utils import send_message, build_directions_list_message, format_direction_with_forms, format_specialty_details, send_message_with_links

def handle_user_message(vk, user_id, peer_id, text, current_state, state_data):
    """Обработка сообщений от обычных пользователей"""
    
    # ========== ВЫБОР УРОВНЯ ==========
    if current_state == 'selecting_level':
        levels = get_education_levels()
        level_dict = {row[1]: row[0] for row in levels}
        if text in level_dict:
            level_id = level_dict[text]
            faculties = get_faculties_by_level(level_id)
            if not faculties:
                send_message(vk, peer_id, f"На уровне «{text}» пока нет направлений.")
                send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
                clear_user_state(user_id)
            else:
                send_message(vk, peer_id, f"Выберите факультет для уровня {text}:", keyboard=build_faculties_keyboard(faculties, page=0))
                set_user_state(user_id, 'selecting_faculty', {'faculties': faculties, 'level_id': level_id, 'level_name': text, 'faculty_page': 0})
        else:
            send_message(vk, peer_id, "Пожалуйста, выберите уровень из списка кнопок.")
        return True
    
    # ========== ВЫБОР ФАКУЛЬТЕТА ==========
    if current_state == 'selecting_faculty':
        faculties = state_data.get('faculties')
        level_id = state_data.get('level_id')
        level_name = state_data.get('level_name')
        
        if not faculties:
            send_message(vk, peer_id, "Что-то пошло не так. Начните заново.", keyboard=build_main_menu_keyboard())
            clear_user_state(user_id)
            return True
        
        # Пагинация
        if text in ["◀ Пред.", "След. ▶"]:
            current_page = state_data.get('faculty_page', 0)
            new_page = current_page - 1 if text == "◀ Пред." else current_page + 1
            send_message(vk, peer_id, f"Выберите факультет для уровня {level_name}:", 
                         keyboard=build_faculties_keyboard(faculties, page=new_page))
            set_user_state(user_id, 'selecting_faculty', {
                'faculties': faculties, 'level_id': level_id, 'level_name': level_name, 'faculty_page': new_page
            })
            return True
        
        selected_faculty = None
        for row in faculties:
            fac_id, fac_name = row[0], row[1]
            if text == fac_name:
                selected_faculty = row
                break
        
        if selected_faculty:
            faculty_id, faculty_name = selected_faculty[0], selected_faculty[1]
            directions = get_directions_by_faculty_and_level(faculty_id, level_id)
            
            if not directions:
                send_message(vk, peer_id, f"На факультете «{faculty_name}» пока нет направлений.")
                current_page = state_data.get('faculty_page', 0)
                send_message(vk, peer_id, "Выберите другой факультет:", keyboard=build_faculties_keyboard(faculties, page=current_page))
            else:
                message = build_directions_list_message(directions, "Доступные направления")
                send_message(vk, peer_id, message)
                send_message(vk, peer_id, "Введите номер направления для подробной информации:")
                set_user_state(user_id, 'selecting_direction', {
                    'directions': directions, 'level_id': level_id, 'level_name': level_name,
                    'faculty_name': faculty_name, 'faculties': faculties,
                    'faculty_page': state_data.get('faculty_page', 0)
                })
        else:
            send_message(vk, peer_id, "Пожалуйста, выберите факультет из кнопок выше.")
        return True
    
    # ========== ВЫБОР НАПРАВЛЕНИЯ ==========
    if current_state == 'selecting_direction':
        directions = state_data.get('directions')
        level_id = state_data.get('level_id')
        level_name = state_data.get('level_name')
        faculty_name = state_data.get('faculty_name')
        faculties = state_data.get('faculties')
        faculty_page = state_data.get('faculty_page', 0)
        from_search = state_data.get('from_search', False)
        
        if not directions:
            send_message(vk, peer_id, "Что-то пошло не так. Начните заново.", keyboard=build_main_menu_keyboard())
            clear_user_state(user_id)
            return True

        # ========== ОБРАБОТКА КНОПОК ПАГИНАЦИИ ==========
        if text in ["◀ Пред.", "След. ▶"]:
            if faculties and level_id and level_name:
                current_page = state_data.get('faculty_page', 0)
                new_page = current_page - 1 if text == "◀ Пред." else current_page + 1
                send_message(vk, peer_id, f"Выберите факультет для уровня {level_name}:", 
                             keyboard=build_faculties_keyboard(faculties, page=new_page))
                set_user_state(user_id, 'selecting_faculty', {
                    'faculties': faculties, 'level_id': level_id, 'level_name': level_name, 'faculty_page': new_page
                })
            else:
                send_message(vk, peer_id, "Выберите уровень образования:", keyboard=build_levels_keyboard())
                set_user_state(user_id, 'selecting_level')
            return True
        
        # ========== Пользователь хочет выбрать другой факультет ==========
        if faculties and text in [fac[1] for fac in faculties]:
            # Находим выбранный факультет
            selected_faculty = None
            for fac in faculties:
                if fac[1] == text:
                    selected_faculty = fac
                    break
            
            if selected_faculty:
                faculty_id, new_faculty_name = selected_faculty[0], selected_faculty[1]
                new_directions = get_directions_by_faculty_and_level(faculty_id, level_id)
                
                if not new_directions:
                    send_message(vk, peer_id, f"На факультете «{new_faculty_name}» пока нет направлений.")
                    send_message(vk, peer_id, f"Выберите факультет для уровня {level_name}:", 
                                 keyboard=build_faculties_keyboard(faculties, page=faculty_page))
                    set_user_state(user_id, 'selecting_faculty', {
                        'faculties': faculties, 'level_id': level_id, 'level_name': level_name, 'faculty_page': faculty_page
                    })
                else:
                    message = f"🎓 Факультет: {new_faculty_name}\n\n"
                    message += build_directions_list_message(new_directions, "Доступные направления")
                    send_message(vk, peer_id, message)
                    send_message(vk, peer_id, "Введите номер направления для подробной информации:")
                    set_user_state(user_id, 'selecting_direction', {
                        'directions': new_directions, 
                        'level_id': level_id, 
                        'level_name': level_name,
                        'faculty_name': new_faculty_name, 
                        'faculties': faculties,
                        'faculty_page': faculty_page,
                        'from_search': from_search
                    })
            return True
        
        # ========== КНОПКА "НАЗАД" ==========
        if text == "◀ Назад":
            # Если пришли из поиска, возвращаемся в главное меню
            if from_search:
                send_message(vk, peer_id, "Выберите интересующий раздел:", keyboard=build_main_menu_keyboard())
                set_user_state(user_id, 'main_menu')
            elif faculties and level_id and level_name:
                send_message(vk, peer_id, f"Выберите факультет для уровня {level_name}:", 
                             keyboard=build_faculties_keyboard(faculties, page=faculty_page))
                set_user_state(user_id, 'selecting_faculty', {
                    'faculties': faculties, 'level_id': level_id, 'level_name': level_name, 'faculty_page': faculty_page
                })
            else:
                send_message(vk, peer_id, "Выберите уровень образования:", keyboard=build_levels_keyboard())
                set_user_state(user_id, 'selecting_level')
            return True
        
        # ========== ОБРАБОТКА НОМЕРА НАПРАВЛЕНИЯ ==========
        try:
            idx = int(text.split('.')[0].strip()) - 1
            if 0 <= idx < len(directions):
                direction_row = directions[idx]
                direction_id = direction_row[0]
                direction = get_direction_with_forms(direction_id)
                
                if not direction:
                    send_message(vk, peer_id, "Информация о направлении не найдена.")
                    send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
                    clear_user_state(user_id)
                elif not direction.get('study_forms'):
                    message = format_direction_with_forms(direction)
                    send_message(vk, peer_id, message)
                    send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
                    clear_user_state(user_id)
                else:
                    message = format_direction_with_forms(direction)
                    send_message(vk, peer_id, message)
                    send_message(vk, peer_id, "Выберите форму обучения из кнопок ниже, для подробной информации:", 
                                 keyboard=build_study_form_keyboard(direction['study_forms']))
                    set_user_state(user_id, 'selecting_study_form', {
                        'study_forms': direction['study_forms'], 
                        'direction_id': direction_id,
                        'level_id': level_id, 
                        'level_name': level_name, 
                        'faculty_name': faculty_name or direction.get('faculty', ''),
                        'faculties': faculties, 
                        'faculty_page': faculty_page, 
                        'directions': directions,
                        'from_search': from_search
                    })
            else:
                send_message(vk, peer_id, f"Некорректный номер. Введите число от 1 до {len(directions)}.")
        except (ValueError, IndexError):
            send_message(vk, peer_id, "Пожалуйста, введите номер направления цифрой или выберите факультет из списка.")
        return True
    
        # ========== ВЫБОР ФОРМЫ ОБУЧЕНИЯ ==========
    if current_state == 'selecting_study_form':
        study_forms = state_data.get('study_forms')
        faculty_name = state_data.get('faculty_name')
        faculties = state_data.get('faculties')
        faculty_page = state_data.get('faculty_page', 0)
        directions = state_data.get('directions')
        level_id = state_data.get('level_id')
        level_name = state_data.get('level_name')
        
        if not study_forms:
            send_message(vk, peer_id, "Что-то пошло не так. Начните заново.", keyboard=build_main_menu_keyboard())
            clear_user_state(user_id)
            return True
        
        # Кнопка "Назад"
        if text == "◀ Назад":
            if directions:
                message = build_directions_list_message(directions, "Доступные направления")
                send_message(vk, peer_id, message)
                send_message(vk, peer_id, "Введите номер направления для подробной информации:")
                set_user_state(user_id, 'selecting_direction', {
                    'directions': directions, 'level_id': level_id, 'level_name': level_name,
                    'faculty_name': faculty_name, 'faculties': faculties, 'faculty_page': faculty_page
                })
            else:
                send_message(vk, peer_id, "Выберите уровень образования:", keyboard=build_levels_keyboard())
                set_user_state(user_id, 'selecting_level')
            return True
        
        found = False
        for i, form in enumerate(study_forms, 1):
            # Преобразуем срок в читаемый формат (как в keyboards.py)
            duration_years = form['duration_years']
            years = int(duration_years)
            months = int(round((duration_years - years) * 12))
            if months == 0:
                duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'}"
            else:
                duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'} {months} {'месяц' if months == 1 else 'месяца' if months in [2,3,4] else 'месяцев'}"
            
            button_text = f"{form['study_form']} (Срок: {duration_text})"
            
            # Сравниваем с текстом кнопки ИЛИ с номером (1, 2, 3...)
            if text == button_text or text == str(i):
                details = get_specialty_details(form['id'])
                message = format_specialty_details(details)
                send_message(vk, peer_id, message)
                send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
                clear_user_state(user_id)
                set_user_state(user_id, 'main_menu')
                found = True
                break
        
        if not found and text not in ["🏠 Меню", "🏠 меню", "◀ Назад"]:
            send_message(vk, peer_id, "Пожалуйста, выберите форму обучения из кнопок выше.")
        return True
    
    # ========== FAQ ==========
    if current_state == 'selecting_faq':
        faq_list = get_all_faq()
        found = False
        for row in faq_list:
            faq_id, question, answer = row[0], row[1], row[2]
            if text == question:
                send_message(vk, peer_id, f"❓ {question}\n\n📝 {answer}")
                found = True
                break
        if found:
            send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
            clear_user_state(user_id)
        elif text not in ["◀ Назад", "🏠 Меню"]:
            send_message(vk, peer_id, "Пожалуйста, выберите вопрос из списка.")
        return True
    
    # ========== ПОИСК ==========
    if current_state == 'searching':
        results = search_directions(text)
        print(f"🔍 Поиск: '{text}', результатов: {len(results)}")  # ВРЕМЕННО
        if not results:
            send_message(vk, peer_id, f"По запросу «{text}» ничего не найдено.\nПопробуйте изменить запрос или воспользуйтесь меню.", keyboard=build_main_menu_keyboard())
            clear_user_state(user_id)
            set_user_state(user_id, 'main_menu')  # ВАЖНО: возвращаем в главное меню
        else:
            lines = [f"🔍 Результаты поиска «{text}»:\n"]
            for i, row in enumerate(results, 1):
                dir_id, code, name, desc, fac_name, lvl_name = row[0], row[1], row[2], row[3], row[4], row[5]
                lines.append(f"{i}. {code} - {name}")
                lines.append(f"   🏛 {fac_name} | 📚 {lvl_name}")
                if desc:
                    lines.append(f"   📖 {desc[:100]}...")
                lines.append("")
            send_message(vk, peer_id, "\n".join(lines))
            
            if len(results) == 1:
                direction_id = results[0][0]
                direction = get_direction_with_forms(direction_id)
                if direction:
                    message = format_direction_with_forms(direction)
                    send_message(vk, peer_id, message)
                    if direction.get('study_forms'):
                        send_message(vk, peer_id, "Введите номер формы обучения для подробной информации:", keyboard=build_study_form_keyboard(direction['study_forms']))
                        set_user_state(user_id, 'selecting_study_form', {'study_forms': direction['study_forms'], 'direction_id': direction_id})
                    else:
                        send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
                        clear_user_state(user_id)
                        set_user_state(user_id, 'main_menu')
                else:
                    send_message(vk, peer_id, "Что будем смотреть дальше?", keyboard=build_main_menu_keyboard())
                    clear_user_state(user_id)
                    set_user_state(user_id, 'main_menu')
            else:
                directions_list = [list(row) for row in results]
                send_message(vk, peer_id, "Введите номер направления для подробной информации:")
                set_user_state(user_id, 'selecting_direction', {'directions': directions_list})
        return True
