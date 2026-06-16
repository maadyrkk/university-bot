from db import db


# ============================================================
# БАЗОВЫЕ CRUD ОПЕРАЦИИ
# ============================================================

def get_education_levels():
    """Получить все уровни образования"""
    return db.fetch_all("SELECT id, name FROM education_levels ORDER BY id")

def add_education_level(name):
    try:
        db.execute("INSERT INTO education_levels (name) VALUES (?)", (name,))
        return True, f"✓ Уровень '{name}' добавлен"
    except:
        return False, f"✗ Уровень '{name}' уже существует"

def delete_education_level(level_id):
    cursor = db.execute("DELETE FROM education_levels WHERE id = ?", (level_id,))
    return cursor.rowcount > 0, f"✓ Уровень удален" if cursor.rowcount > 0 else "✗ Уровень не найден"

def edit_education_level(level_id, new_name):
    cursor = db.execute("UPDATE education_levels SET name = ? WHERE id = ?", (new_name, level_id))
    return cursor.rowcount > 0, f"✓ Уровень обновлен" if cursor.rowcount > 0 else "✗ Уровень не найден"

def get_faculties():
    """Получить все факультеты"""
    return db.fetch_all("SELECT id, name FROM faculties ORDER BY id")

def add_faculty(name):
    try:
        db.execute("INSERT INTO faculties (name) VALUES (?)", (name,))
        return True, f"✓ Факультет '{name}' добавлен"
    except:
        return False, f"✗ Факультет '{name}' уже существует"

def delete_faculty(faculty_id):
    cursor = db.execute("DELETE FROM faculties WHERE id = ?", (faculty_id,))
    return cursor.rowcount > 0, f"✓ Факультет удален" if cursor.rowcount > 0 else "✗ Факультет не найден"

def edit_faculty(faculty_id, new_name):
    cursor = db.execute("UPDATE faculties SET name = ? WHERE id = ?", (new_name, faculty_id))
    return cursor.rowcount > 0, f"✓ Факультет обновлен" if cursor.rowcount > 0 else "✗ Факультет не найден"

def get_all_subjects():
    """Получить все предметы ЕГЭ"""
    return db.fetch_all("SELECT id, name, minimum_score FROM subjects ORDER BY id")

def add_subject(name, min_score):
    try:
        db.execute("INSERT INTO subjects (name, minimum_score) VALUES (?, ?)", (name, min_score))
        return True, f"✓ Предмет '{name}' добавлен"
    except:
        return False, f"✗ Предмет '{name}' уже существует"

def delete_subject(subject_id):
    cursor = db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    return cursor.rowcount > 0, f"✓ Предмет удален" if cursor.rowcount > 0 else "✗ Предмет не найден"

def edit_subject(subject_id, new_name, new_min_score):
    cursor = db.execute("UPDATE subjects SET name = ?, minimum_score = ? WHERE id = ?", 
                       (new_name, new_min_score, subject_id))
    return cursor.rowcount > 0, f"✓ Предмет обновлен" if cursor.rowcount > 0 else "✗ Предмет не найден"

def get_all_entrance_exams():
    """Получить все вступительные испытания"""
    return db.fetch_all("SELECT id, name, minimum_score, description FROM entrance_exams ORDER BY id")

def add_entrance_exam(name, min_score, description=None):
    try:
        db.execute("INSERT INTO entrance_exams (name, minimum_score, description) VALUES (?, ?, ?)", 
                   (name, min_score, description))
        return True, f"✓ ВИ '{name}' добавлено"
    except:
        return False, f"✗ ВИ '{name}' уже существует"

def delete_entrance_exam(exam_id):
    cursor = db.execute("DELETE FROM entrance_exams WHERE id = ?", (exam_id,))
    return cursor.rowcount > 0, f"✓ ВИ удалено" if cursor.rowcount > 0 else "✗ ВИ не найдено"

def edit_entrance_exam(exam_id, new_name, new_min_score, new_description=None):
    cursor = db.execute("UPDATE entrance_exams SET name = ?, minimum_score = ?, description = ? WHERE id = ?", 
                       (new_name, new_min_score, new_description, exam_id))
    return cursor.rowcount > 0, f"✓ ВИ обновлено" if cursor.rowcount > 0 else "✗ ВИ не найдено"

def get_all_programs():
    """Получить все программы обучения"""
    return db.fetch_all('''
        SELECT s.id, d.code, d.name, s.study_form, s.duration_years, 
               s.budget_places, s.paid_places, s.tuition_fee
        FROM specialties s
        JOIN directions d ON s.direction_id = d.id
        ORDER BY s.id
    ''')

def get_all_directions():
    """Получить все направления подготовки"""
    return db.fetch_all('''
        SELECT d.id, d.code, d.name, d.description, f.name, el.name
        FROM directions d
        JOIN faculties f ON d.id_faculty = f.id
        JOIN education_levels el ON d.id_level = el.id
        ORDER BY d.id
    ''')

def get_faculties_by_level(level_id):
    """Получить факультеты, на которых есть направления указанного уровня"""
    return db.fetch_all('''
        SELECT DISTINCT f.id, f.name
        FROM faculties f
        JOIN directions d ON d.id_faculty = f.id
        WHERE d.id_level = ?
        ORDER BY f.name
    ''', (level_id,))

def get_directions_by_faculty_and_level(faculty_id, level_id):
    """Получить направления на факультете с указанным уровнем"""
    return db.fetch_all('''
        SELECT d.id, d.code, d.name, d.description
        FROM directions d
        WHERE d.id_faculty = ? AND d.id_level = ?
        ORDER BY d.code, d.id
    ''', (faculty_id, level_id))

def get_direction_details(direction_id):
    """Получить детальную информацию о направлении"""
    row = db.fetch_one('''
        SELECT d.code, d.name, d.description, f.name, el.name
        FROM directions d
        JOIN faculties f ON d.id_faculty = f.id
        JOIN education_levels el ON d.id_level = el.id
        WHERE d.id = ?
    ''', (direction_id,))
    
    if not row:
        return None
    
    required_rows = db.fetch_all('''
        SELECT sub.name, sub.minimum_score
        FROM required_subjects rs
        JOIN subjects sub ON rs.subject_id = sub.id
        WHERE rs.direction_id = ?
        ORDER BY sub.name
    ''', (direction_id,))
    
    elective_rows = db.fetch_all('''
        SELECT sub.name, sub.minimum_score
        FROM elective_subjects es
        JOIN subjects sub ON es.subject_id = sub.id
        WHERE es.direction_id = ?
        ORDER BY sub.name
    ''', (direction_id,))
    
    exam_rows = db.fetch_all('''
        SELECT ex.name, ex.minimum_score, ex.description
        FROM required_entrance_exams re
        JOIN entrance_exams ex ON re.exam_id = ex.id
        WHERE re.direction_id = ?
        ORDER BY ex.name
    ''', (direction_id,))
    
    return {
        'code': row[0],
        'name': row[1],
        'description': row[2] or '',
        'faculty': row[3],
        'level': row[4],
        'required_subjects': [{'name': r[0], 'min_score': r[1]} for r in required_rows],
        'elective_subjects': [{'name': r[0], 'min_score': r[1]} for r in elective_rows],
        'required_exams': [{'name': r[0], 'min_score': r[1], 'description': r[2]} for r in exam_rows]
    }

def get_direction_with_forms(direction_id):
    """Получить направление с формами обучения"""
    direction = get_direction_details(direction_id)
    if not direction:
        return None
    forms = get_specialties_by_direction(direction_id)
    direction['study_forms'] = forms
    return direction

def get_specialties_by_direction(direction_id):
    """Получить формы обучения для направления"""
    rows = db.fetch_all('''
        SELECT s.id, s.study_form, s.duration_years, 
               s.budget_places, s.paid_places, s.tuition_fee
        FROM specialties s
        WHERE s.direction_id = ?
        ORDER BY s.id
    ''', (direction_id,))
    
    form_order = {'Очная': 1, 'Очно-заочная': 2, 'Заочная': 3}
    result = []
    for row in rows:
        result.append({
            'id': row[0],
            'study_form': row[1],
            'duration_years': row[2],
            'budget_places': row[3],
            'paid_places': row[4],
            'tuition_fee': row[5]
        })
    result.sort(key=lambda x: form_order.get(x['study_form'], 999))
    return result

def get_specialty_details(specialty_id):
    """Получить детальную информацию о форме обучения"""
    row = db.fetch_one('''
        SELECT s.study_form, s.duration_years, s.budget_places, s.paid_places, s.tuition_fee,
               d.id, d.code, d.name, d.description, f.name, el.name
        FROM specialties s
        JOIN directions d ON s.direction_id = d.id
        JOIN faculties f ON d.id_faculty = f.id
        JOIN education_levels el ON d.id_level = el.id
        WHERE s.id = ?
    ''', (specialty_id,))
    
    if not row:
        return None
    
    direction_id = row[5]
    
    required_rows = db.fetch_all('''
        SELECT sub.name, sub.minimum_score
        FROM required_subjects rs
        JOIN subjects sub ON rs.subject_id = sub.id
        WHERE rs.direction_id = ?
        ORDER BY sub.name
    ''', (direction_id,))
    
    elective_rows = db.fetch_all('''
        SELECT sub.name, sub.minimum_score
        FROM elective_subjects es
        JOIN subjects sub ON es.subject_id = sub.id
        WHERE es.direction_id = ?
        ORDER BY sub.name
    ''', (direction_id,))
    
    exam_rows = db.fetch_all('''
        SELECT ex.name, ex.minimum_score, ex.description
        FROM required_entrance_exams re
        JOIN entrance_exams ex ON re.exam_id = ex.id
        WHERE re.direction_id = ?
        ORDER BY ex.name
    ''', (direction_id,))
    
    return {
        'specialty_id': specialty_id,
        'direction_id': direction_id,
        'code': row[6],
        'name': row[7],
        'description': row[8] or '',
        'faculty': row[9],
        'level': row[10],
        'study_form': row[0],
        'duration_years': row[1],
        'budget_places': row[2],
        'paid_places': row[3],
        'tuition_fee': row[4],
        'required_subjects': [{'name': r[0], 'min_score': r[1]} for r in required_rows],
        'elective_subjects': [{'name': r[0], 'min_score': r[1]} for r in elective_rows],
        'required_exams': [{'name': r[0], 'min_score': r[1], 'description': r[2]} for r in exam_rows]
    }

def get_all_faq(category=None):
    """Получить все вопросы FAQ (опционально по категории)"""
    if category:
        return db.fetch_all(
            "SELECT id, question, answer FROM faq WHERE category = ? ORDER BY sort_order, id",
            (category,)
        )
    return db.fetch_all("SELECT id, question, answer FROM faq ORDER BY sort_order, id")

def get_faq_categories():
    """Получить все категории FAQ"""
    return db.fetch_all("SELECT DISTINCT category FROM faq ORDER BY category")

def get_commission_info():
    """Получить информацию о приёмной комиссии"""
    return db.fetch_all('''
        SELECT id, question, answer, sort_order 
        FROM faq 
        WHERE category = 'commission' 
        ORDER BY sort_order
    ''')

def get_commission_text():
    """Сформировать текст для кнопки 'О приёмной комиссии'"""
    info = get_commission_info()
    if not info:
        return "Информация о приёмной комиссии временно недоступна."
    
    lines = ["🏛 ПРИЁМНАЯ КОМИССИЯ ТУВГУ\n"]
    
    for row in info:
        faq_id, question, answer, sort_order = row[0], row[1], row[2], row[3]
        lines.append(f"{question}: {answer}")
    
    return "\n".join(lines)

def add_faq(question, answer, category='faq'):
    """Добавить вопрос в FAQ с категорией"""
    max_order = db.fetch_one("SELECT MAX(sort_order) FROM faq WHERE category = ?", (category,))[0] or 0
    db.execute("INSERT INTO faq (question, answer, category, sort_order) VALUES (?, ?, ?, ?)",
               (question, answer, category, max_order + 1))
    return True, f"✓ Вопрос добавлен в категорию '{category}'"

def get_faq_by_category(category):
    """Получить FAQ по категории"""
    return db.fetch_all('''
        SELECT id, question, answer, sort_order 
        FROM faq 
        WHERE category = ? 
        ORDER BY sort_order
    ''', (category,))

def delete_faq(faq_id):
    cursor = db.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
    return cursor.rowcount > 0, f"✓ Вопрос удален" if cursor.rowcount > 0 else "✗ Вопрос не найден"

def edit_faq(faq_id, new_question, new_answer):
    cursor = db.execute("UPDATE faq SET question = ?, answer = ? WHERE id = ?", 
                       (new_question, new_answer, faq_id))
    return cursor.rowcount > 0, f"✓ Вопрос обновлен" if cursor.rowcount > 0 else "✗ Вопрос не найден"

def search_directions(keyword):
    """Поиск направлений по коду"""
    if not keyword or len(keyword.strip()) == 0:
        return []
    
    keyword_lower = keyword.lower().strip()
    
    
    results = db.fetch_all('''
        SELECT DISTINCT d.id, d.code, d.name, d.description, f.name, el.name
        FROM directions d
        JOIN faculties f ON d.id_faculty = f.id
        JOIN education_levels el ON d.id_level = el.id
        WHERE LOWER(d.code) LIKE ?
        ORDER BY d.id
        LIMIT 10
    ''', (f'%{keyword_lower}%',))
    
    return results

def get_stats():
    """Получить статистику базы данных"""
    return {
        'levels': db.fetch_one('SELECT COUNT(*) FROM education_levels')[0],
        'faculties': db.fetch_one('SELECT COUNT(*) FROM faculties')[0],
        'subjects': db.fetch_one('SELECT COUNT(*) FROM subjects')[0],
        'entrance_exams': db.fetch_one('SELECT COUNT(*) FROM entrance_exams')[0],
        'directions': db.fetch_one('SELECT COUNT(*) FROM directions')[0],
        'programs': db.fetch_one('SELECT COUNT(*) FROM specialties')[0],
        'faq': db.fetch_one('SELECT COUNT(*) FROM faq')[0],
    }

def add_direction(code, name, description, faculty_id, level_id):
    """Добавить новое направление подготовки"""
    try:
        db.execute('''
            INSERT INTO directions (code, name, description, id_faculty, id_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, name, description, faculty_id, level_id))
        return True, f"✓ Направление '{code} - {name}' добавлено"
    except Exception as e:
        return False, f"✗ Ошибка: {e}"

def delete_direction(direction_id):
    """Удалить направление подготовки"""
    try:
        # Сначала удаляем связанные записи
        db.execute("DELETE FROM required_subjects WHERE direction_id = ?", (direction_id,))
        db.execute("DELETE FROM elective_subjects WHERE direction_id = ?", (direction_id,))
        db.execute("DELETE FROM required_entrance_exams WHERE direction_id = ?", (direction_id,))
        db.execute("DELETE FROM specialties WHERE direction_id = ?", (direction_id,))
        
        cursor = db.execute("DELETE FROM directions WHERE id = ?", (direction_id,))
        return cursor.rowcount > 0, f"✓ Направление удалено" if cursor.rowcount > 0 else "✗ Направление не найдено"
    except Exception as e:
        return False, f"✗ Ошибка: {e}"

def edit_direction(direction_id, code, name, description, faculty_id, level_id):
    """Редактировать направление подготовки"""
    try:
        cursor = db.execute('''
            UPDATE directions 
            SET code = ?, name = ?, description = ?, id_faculty = ?, id_level = ?
            WHERE id = ?
        ''', (code, name, description, faculty_id, level_id, direction_id))
        return cursor.rowcount > 0, f"✓ Направление обновлено" if cursor.rowcount > 0 else "✗ Направление не найдено"
    except Exception as e:
        return False, f"✗ Ошибка: {e}"

def get_direction_by_id(direction_id):
    """Получить направление по ID"""
    return db.fetch_one('''
        SELECT d.id, d.code, d.name, d.description, d.id_faculty, d.id_level,
               f.name as faculty_name, el.name as level_name
        FROM directions d
        JOIN faculties f ON d.id_faculty = f.id
        JOIN education_levels el ON d.id_level = el.id
        WHERE d.id = ?
    ''', (direction_id,))

def get_all_faculties_list():
    """Получить список всех факультетов (для выбора)"""
    return db.fetch_all("SELECT id, name FROM faculties ORDER BY id")

def get_all_levels_list():
    """Получить список всех уровней образования (для выбора)"""
    return db.fetch_all("SELECT id, name FROM education_levels ORDER BY id")

def get_direction_subjects(direction_id):
    """Получить все предметы для направления (обязательные и на выбор)"""
    required = db.fetch_all('''
        SELECT s.id, s.name, s.minimum_score
        FROM required_subjects rs
        JOIN subjects s ON rs.subject_id = s.id
        WHERE rs.direction_id = ?
        ORDER BY s.name
    ''', (direction_id,))
    
    elective = db.fetch_all('''
        SELECT s.id, s.name, s.minimum_score
        FROM elective_subjects es
        JOIN subjects s ON es.subject_id = s.id
        WHERE es.direction_id = ?
        ORDER BY s.name
    ''', (direction_id,))
    
    return {'required': required, 'elective': elective}

def get_direction_exams(direction_id):
    """Получить все ВИ для направления"""
    return db.fetch_all('''
        SELECT e.id, e.name, e.minimum_score, e.description
        FROM required_entrance_exams re
        JOIN entrance_exams e ON re.exam_id = e.id
        WHERE re.direction_id = ?
        ORDER BY e.name
    ''', (direction_id,))

def add_required_subject(direction_id, subject_id):
    """Добавить обязательный предмет к направлению"""
    try:
        db.execute('''
            INSERT INTO required_subjects (direction_id, subject_id)
            VALUES (?, ?)
        ''', (direction_id, subject_id))
        return True, "✓ Обязательный предмет добавлен"
    except:
        return False, "✗ Предмет уже добавлен или ошибка"

def remove_required_subject(direction_id, subject_id):
    """Удалить обязательный предмет из направления"""
    cursor = db.execute('''
        DELETE FROM required_subjects 
        WHERE direction_id = ? AND subject_id = ?
    ''', (direction_id, subject_id))
    return cursor.rowcount > 0, "✓ Предмет удален" if cursor.rowcount > 0 else "✗ Предмет не найден"

def add_elective_subject(direction_id, subject_id):
    """Добавить предмет на выбор к направлению"""
    try:
        db.execute('''
            INSERT INTO elective_subjects (direction_id, subject_id)
            VALUES (?, ?)
        ''', (direction_id, subject_id))
        return True, "✓ Предмет на выбор добавлен"
    except:
        return False, "✗ Предмет уже добавлен или ошибка"

def remove_elective_subject(direction_id, subject_id):
    """Удалить предмет на выбор из направления"""
    cursor = db.execute('''
        DELETE FROM elective_subjects 
        WHERE direction_id = ? AND subject_id = ?
    ''', (direction_id, subject_id))
    return cursor.rowcount > 0, "✓ Предмет удален" if cursor.rowcount > 0 else "✗ Предмет не найден"

def add_required_exam(direction_id, exam_id):
    """Добавить ВИ к направлению"""
    try:
        db.execute('''
            INSERT INTO required_entrance_exams (direction_id, exam_id)
            VALUES (?, ?)
        ''', (direction_id, exam_id))
        return True, "✓ ВИ добавлено"
    except:
        return False, "✗ ВИ уже добавлено или ошибка"

def remove_required_exam(direction_id, exam_id):
    """Удалить ВИ из направления"""
    cursor = db.execute('''
        DELETE FROM required_entrance_exams 
        WHERE direction_id = ? AND exam_id = ?
    ''', (direction_id, exam_id))
    return cursor.rowcount > 0, "✓ ВИ удалено" if cursor.rowcount > 0 else "✗ ВИ не найдено"

def get_all_subjects_list():
    """Получить список всех предметов для выбора"""
    return db.fetch_all("SELECT id, name, minimum_score FROM subjects ORDER BY id")

def get_all_exams_list():
    """Получить список всех ВИ для выбора"""
    return db.fetch_all("SELECT id, name, minimum_score FROM entrance_exams ORDER BY id")



def get_all_programs_list():
    """Получить список всех программ с подробной информацией"""
    return db.fetch_all('''
        SELECT s.id, d.code, d.name, s.study_form, s.duration_years, 
               s.budget_places, s.paid_places, s.tuition_fee, d.id as direction_id
        FROM specialties s
        JOIN directions d ON s.direction_id = d.id
        ORDER BY s.id
    ''')

def get_program_by_id(program_id):
    """Получить программу по ID"""
    return db.fetch_one('''
        SELECT s.id, s.direction_id, d.code, d.name, s.study_form, 
               s.duration_years, s.budget_places, s.paid_places, s.tuition_fee
        FROM specialties s
        JOIN directions d ON s.direction_id = d.id
        WHERE s.id = ?
    ''', (program_id,))

def add_program(direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee):
    """Добавить новую программу обучения"""
    try:
        db.execute('''
            INSERT INTO specialties (direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee))
        return True, "✓ Программа добавлена"
    except Exception as e:
        return False, f"✗ Ошибка: {e}"

def edit_program(program_id, direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee):
    """Редактировать программу обучения"""
    try:
        cursor = db.execute('''
            UPDATE specialties 
            SET direction_id = ?, study_form = ?, duration_years = ?, 
                budget_places = ?, paid_places = ?, tuition_fee = ?
            WHERE id = ?
        ''', (direction_id, study_form, duration_years, budget_places, paid_places, tuition_fee, program_id))
        return cursor.rowcount > 0, "✓ Программа обновлена" if cursor.rowcount > 0 else "✗ Программа не найдена"
    except Exception as e:
        return False, f"✗ Ошибка: {e}"

def delete_program(program_id):
    """Удалить программу обучения"""
    try:
        cursor = db.execute("DELETE FROM specialties WHERE id = ?", (program_id,))
        return cursor.rowcount > 0, "✓ Программа удалена" if cursor.rowcount > 0 else "✗ Программа не найдена"
    except Exception as e:
        return False, f"✗ Ошибка: {e}"

def get_all_directions_for_select():
    """Получить список направлений для выбора (ID, код, название)"""
    return db.fetch_all('''
        SELECT d.id, d.code, d.name, f.name as faculty_name, el.name as level_name
        FROM directions d
        JOIN faculties f ON d.id_faculty = f.id
        JOIN education_levels el ON d.id_level = el.id
        ORDER BY d.id
    ''')
