from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from models import get_education_levels, get_all_faq

def build_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Уровни образования", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Поиск", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("О приёмной комиссии", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("Часто задаваемые вопросы", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_admin_menu_keyboard():
    """Клавиатура админ-панели"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📊 Статистика", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📚 Уровни образования", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("🏛 Факультеты", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📖 Предметы ЕГЭ", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("🎓 ВИ (вступительные)", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📋 Направления", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("📚 Программы", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("Часто задаваемые вопросы (ред.)", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📢 Рассылка", color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()

def build_broadcast_keyboard():
    """Клавиатура меню рассылки"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📊 Статистика рассылки", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⏰ Отложенная рассылка", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📋 Список пользователей", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📜 История рассылок", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_crud_keyboard():
    """Базовая CRUD-клавиатура"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("➕ Добавить", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("✏️ Редактировать", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("❌ Удалить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📋 Список", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_directions_crud_keyboard():
    """CRUD-клавиатура для направлений (с доп. кнопками для предметов и ВИ)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("➕ Добавить", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("✏️ Редактировать", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📚 Обязательные предметы", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📖 Предметы на выбор", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🎓 ВИ", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("❌ Удалить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("📋 Список", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_levels_keyboard():
    """Клавиатура выбора уровня образования"""
    keyboard = VkKeyboard(one_time=False)
    levels = get_education_levels()
    for i in range(0, len(levels), 2):
        if i < len(levels):
            keyboard.add_button(levels[i][1], color=VkKeyboardColor.PRIMARY)
        if i + 1 < len(levels):
            keyboard.add_button(levels[i+1][1], color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button("🏠 Меню", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_faculties_keyboard(faculties, page=0, per_page=5):
    """Клавиатура выбора факультета с пагинацией"""
    keyboard = VkKeyboard(one_time=False)
    start = page * per_page
    end = start + per_page
    page_faculties = faculties[start:end]
    
    for row in page_faculties:
        fac_id, name = row[0], row[1]
        keyboard.add_button(name, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append("◀ Пред.")
    if end < len(faculties):
        nav_buttons.append("След. ▶")
    
    if nav_buttons:
        for btn in nav_buttons:
            keyboard.add_button(btn, color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    
    keyboard.add_button("🏠 Меню", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_faq_keyboard():
    """Клавиатура выбора вопроса из FAQ"""
    keyboard = VkKeyboard(one_time=False)
    faq_list = get_all_faq()
    for row in faq_list:
        question = row[1]
        keyboard.add_button(question, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button("🏠 Меню", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_study_form_keyboard(study_forms):
    """Клавиатура выбора формы обучения (срок в годах и месяцах)"""
    keyboard = VkKeyboard(one_time=False)
    for form in study_forms:
        duration_years = form['duration_years']
        # Преобразуем десятичный формат в годы и месяцы
        years = int(duration_years)
        months = int(round((duration_years - years) * 12))
        if months == 0:
            duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'}"
        else:
            duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'} {months} {'месяц' if months == 1 else 'месяца' if months in [2,3,4] else 'месяцев'}"
        
        text = f"{form['study_form']} (Срок: {duration_text})"
        keyboard.add_button(text, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🏠 Меню", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_scheduled_menu_keyboard():
    """Клавиатура меню отложенной рассылки"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📅 Создать отложенную", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📋 Список запланированных", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("❌ Отменить рассылку", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_scheduled_compose_keyboard():
    """Клавиатура для создания отложенной рассылки"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("➕ Добавить ещё", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("✅ Завершить", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("❌ Отменить", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def build_subjects_management_keyboard():
    """Клавиатура для управления предметами (без редактирования)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("➕ Добавить", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("❌ Удалить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📋 Список", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def build_faq_admin_keyboard():
    """Клавиатура для администрирования FAQ"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📋 Обычные вопросы", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🏛 Приёмная комиссия", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("➕ Добавить", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("◀ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()
