import json
from vk_api.utils import get_random_id

def send_message(vk, peer_id, message, keyboard=None):
    """Универсальная функция отправки сообщения"""
    params = {'peer_id': peer_id, 'message': message, 'random_id': get_random_id()}
    if keyboard:
        params['keyboard'] = keyboard
    try:
        vk.messages.send(**params)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def send_message_with_links(vk, peer_id, message, texts, urls):
    """Отправка сообщения с кнопками-ссылками"""
    if not texts or not urls:
        send_message(vk, peer_id, message)
        return
    buttons = []
    for btn_text, btn_url in zip(texts.split(','), urls.split(',')):
        btn_text, btn_url = btn_text.strip(), btn_url.strip()
        if btn_text and btn_url:
            buttons.append([{"action": {"type": "open_link", "link": btn_url, "label": btn_text}}])
    keyboard = json.dumps({"inline": True, "buttons": buttons}, ensure_ascii=False)
    send_message(vk, peer_id, message, keyboard=keyboard)

def build_directions_list_message(directions, title="Доступные направления"):
    """Формирование сообщения со списком направлений"""
    if not directions:
        return f"{title} не найдены."
    lines = [f"{title}:\n"]
    for i, row in enumerate(directions, 1):
        dir_id, code, name, description = row[0], row[1], row[2], row[3]
        lines.append(f"{i}. {code} - {name}")
        if description:
            lines.append(f"   📖 {description[:100]}..." if len(description) > 100 else f"   📖 {description}")
        lines.append("")
    return "\n".join(lines)

def format_direction_with_forms(direction):
    """Форматирование информации о направлении с формами обучения"""
    if not direction:
        return "Информация не найдена."
    
    lines = [
        f"🏫 {direction['code']} - {direction['name']}",
        f"📚 {direction['level']}",
        f"🏛 {direction['faculty']}",
        f"📝 {direction['description']}" if direction['description'] else "",
        ""
    ]
    return "\n".join(lines)

def format_specialty_details(details):
    """Форматирование детальной информации о форме обучения"""
    if not details:
        return "Информация не найдена."
    
    # Преобразуем срок обучения в годы и месяцы
    duration_years = details['duration_years']
    years = int(duration_years)
    months = int(round((duration_years - years) * 12))
    if months == 0:
        duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'}"
    else:
        duration_text = f"{years} {'год' if years == 1 else 'года' if years in [2,3,4] else 'лет'} {months} {'месяц' if months == 1 else 'месяца' if months in [2,3,4] else 'месяцев'}"
    
    lines = [
        f"🏫 {details['code']} - {details['name']}",
        f"📚 {details['level']}",
        f"🏛 {details['faculty']}",
        f"📝 {details['description']}" if details['description'] else "",
        "",
        f"🎓 Форма обучения: {details['study_form']}",
        f"⏱ Срок обучения: {duration_text}",
        "",
        "💰 Места и стоимость:",
        f"   • Бюджетных мест: {details['budget_places']}",
        f"   • Платных мест: {details['paid_places']}",
        f"   • Стоимость: {details['tuition_fee']:,.0f} руб/год"
    ]
    
    # Добавляем обязательные предметы ТОЛЬКО если они есть
    if details.get('required_subjects') and len(details['required_subjects']) > 0:
        lines.append("")
        lines.append("📝 Обязательные предметы ЕГЭ:")
        for subj in details['required_subjects']:
            lines.append(f"  • {subj['name']} (мин. {subj['min_score']} баллов)")
    
    if details.get('elective_subjects') and len(details['elective_subjects']) > 0:
        lines.append("")
        lines.append("📝 Предметы ЕГЭ на выбор:")
        for subj in details['elective_subjects']:
            lines.append(f"  • {subj['name']} (мин. {subj['min_score']} баллов)")
    
    if details.get('required_exams') and len(details['required_exams']) > 0:
        lines.append("")
        lines.append("🎓 Вступительные испытания (ВИ):")
        for exam in details['required_exams']:
            desc = f" ({exam['description']})" if exam['description'] else ""
            lines.append(f"  • {exam['name']}{desc} (мин. {exam['min_score']} баллов)")
    
    return "\n".join(lines)
