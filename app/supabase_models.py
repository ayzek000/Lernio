from app.supabase_client import get_supabase_client, get_supabase_admin_client
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import uuid

supabase = get_supabase_client()
supabase_admin = get_supabase_admin_client()

class SupabaseUser:
    """Адаптер для работы с пользователями в Supabase"""
    
    @staticmethod
    def create(username, password, role='student', full_name=None):
        """Создает нового пользователя"""
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
        
        user_data = {
            'id': user_id,
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'full_name': full_name,
            'registration_date': datetime.utcnow().isoformat(),
        }
        
        response = supabase_admin.table('users').insert(user_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(user_id):
        """Получает пользователя по ID"""
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_username(username):
        """Получает пользователя по имени пользователя"""
        response = supabase.table('users').select('*').eq('username', username).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def update(user_id, data):
        """Обновляет данные пользователя"""
        response = supabase.table('users').update(data).eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(user_id):
        """Удаляет пользователя"""
        response = supabase_admin.table('users').delete().eq('id', user_id).execute()
        return True if response.data else False
    
    @staticmethod
    def check_password(user_data, password):
        """Проверяет пароль пользователя"""
        return check_password_hash(user_data['password_hash'], password)
    
    @staticmethod
    def set_password(user_id, password):
        """Устанавливает новый пароль пользователя"""
        password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
        return SupabaseUser.update(user_id, {'password_hash': password_hash})
    
    @staticmethod
    def update_last_login(user_id):
        """Обновляет время последнего входа пользователя"""
        return SupabaseUser.update(user_id, {'last_login': datetime.utcnow().isoformat()})


# Аналогичные адаптеры можно создать для других моделей
class SupabaseLesson:
    """Адаптер для работы с уроками в Supabase"""
    
    @staticmethod
    def create(title, description=None, order=0):
        """Создает новый урок"""
        lesson_id = str(uuid.uuid4())
        
        lesson_data = {
            'id': lesson_id,
            'title': title,
            'description': description,
            'order': order,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('lessons').insert(lesson_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(lesson_id):
        """Получает урок по ID"""
        response = supabase.table('lessons').select('*').eq('id', lesson_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_all(order_by='order'):
        """Получает все уроки, отсортированные по указанному полю"""
        response = supabase.table('lessons').select('*').order(order_by).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(lesson_id, data):
        """Обновляет данные урока"""
        response = supabase.table('lessons').update(data).eq('id', lesson_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(lesson_id):
        """Удаляет урок"""
        response = supabase.table('lessons').delete().eq('id', lesson_id).execute()
        return True if response.data else False


class SupabaseMaterial:
    """Адаптер для работы с материалами в Supabase"""
    
    @staticmethod
    def create(lesson_id, title, content=None, material_type="text", storage_path=None, position=0):
        """Создает новый материал"""
        material_id = str(uuid.uuid4())
        
        material_data = {
            'id': material_id,
            'lesson_id': lesson_id,
            'title': title,
            'content': content,
            'material_type': material_type,
            'storage_path': storage_path,
            'position': position,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('materials').insert(material_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(material_id):
        """Получает материал по ID"""
        response = supabase.table('materials').select('*').eq('id', material_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_lesson(lesson_id, order_by="position"):
        """Получает все материалы урока, отсортированные по указанному полю"""
        response = supabase.table('materials').select('*').eq('lesson_id', lesson_id).order(order_by).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(material_id, data):
        """Обновляет данные материала"""
        response = supabase.table('materials').update(data).eq('id', material_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(material_id):
        """Удаляет материал"""
        response = supabase.table('materials').delete().eq('id', material_id).execute()
        return True if response.data else False


class SupabaseTest:
    """Адаптер для работы с тестами в Supabase"""
    
    @staticmethod
    def create(lesson_id, title, description=None):
        """Создает новый тест"""
        test_id = str(uuid.uuid4())
        
        test_data = {
            'id': test_id,
            'lesson_id': lesson_id,
            'title': title,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('tests').insert(test_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(test_id):
        """Получает тест по ID"""
        response = supabase.table('tests').select('*').eq('id', test_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_lesson(lesson_id):
        """Получает все тесты урока"""
        response = supabase.table('tests').select('*').eq('lesson_id', lesson_id).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(test_id, data):
        """Обновляет данные теста"""
        response = supabase.table('tests').update(data).eq('id', test_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(test_id):
        """Удаляет тест"""
        response = supabase.table('tests').delete().eq('id', test_id).execute()
        return True if response.data else False


class SupabaseQuestion:
    """Адаптер для работы с вопросами в Supabase"""
    
    @staticmethod
    def create(test_id, text, question_type="single_choice", options=None, correct_answer=None):
        """Создает новый вопрос"""
        question_id = str(uuid.uuid4())
        
        # Преобразуем списки в JSON для хранения в базе данных
        options_json = json.dumps(options) if options else None
        correct_answer_json = json.dumps(correct_answer) if correct_answer else None
        
        question_data = {
            'id': question_id,
            'test_id': test_id,
            'text': text,
            'question_type': question_type,
            'options': options_json,
            'correct_answer': correct_answer_json,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('questions').insert(question_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(question_id):
        """Получает вопрос по ID"""
        response = supabase.table('questions').select('*').eq('id', question_id).execute()
        if not response.data:
            return None
        
        question = response.data[0]
        
        # Преобразуем JSON обратно в списки
        if question.get('options'):
            question['options'] = json.loads(question['options'])
        if question.get('correct_answer'):
            question['correct_answer'] = json.loads(question['correct_answer'])
        
        return question
    
    @staticmethod
    def get_by_test(test_id):
        """Получает все вопросы теста"""
        response = supabase.table('questions').select('*').eq('test_id', test_id).execute()
        if not response.data:
            return []
        
        questions = response.data
        
        # Преобразуем JSON обратно в списки для каждого вопроса
        for question in questions:
            if question.get('options'):
                question['options'] = json.loads(question['options'])
            if question.get('correct_answer'):
                question['correct_answer'] = json.loads(question['correct_answer'])
        
        return questions
    
    @staticmethod
    def update(question_id, data):
        """Обновляет данные вопроса"""
        # Преобразуем списки в JSON для хранения в базе данных
        if 'options' in data and data['options'] is not None:
            data['options'] = json.dumps(data['options'])
        if 'correct_answer' in data and data['correct_answer'] is not None:
            data['correct_answer'] = json.dumps(data['correct_answer'])
        
        response = supabase.table('questions').update(data).eq('id', question_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(question_id):
        """Удаляет вопрос"""
        response = supabase.table('questions').delete().eq('id', question_id).execute()
        return True if response.data else False


class SupabaseSubmission:
    """Адаптер для работы с ответами на тесты в Supabase"""
    
    @staticmethod
    def create(test_id, student_id, answers=None, score=None):
        """Создает новый ответ на тест"""
        submission_id = str(uuid.uuid4())
        
        # Преобразуем ответы в JSON для хранения в базе данных
        answers_json = json.dumps(answers) if answers else None
        
        submission_data = {
            'id': submission_id,
            'test_id': test_id,
            'student_id': student_id,
            'answers': answers_json,
            'score': score,
            'submitted_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('submissions').insert(submission_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(submission_id):
        """Получает ответ на тест по ID"""
        response = supabase.table('submissions').select('*').eq('id', submission_id).execute()
        if not response.data:
            return None
        
        submission = response.data[0]
        
        # Преобразуем JSON обратно в словарь
        if submission.get('answers'):
            submission['answers'] = json.loads(submission['answers'])
        
        return submission
    
    @staticmethod
    def get_by_student(student_id):
        """Получает все ответы на тесты студента"""
        response = supabase.table('submissions').select('*').eq('student_id', student_id).execute()
        if not response.data:
            return []
        
        submissions = response.data
        
        # Преобразуем JSON обратно в словарь для каждого ответа
        for submission in submissions:
            if submission.get('answers'):
                submission['answers'] = json.loads(submission['answers'])
        
        return submissions
    
    @staticmethod
    def get_by_test(test_id):
        """Получает все ответы на тест"""
        response = supabase.table('submissions').select('*').eq('test_id', test_id).execute()
        if not response.data:
            return []
        
        submissions = response.data
        
        # Преобразуем JSON обратно в словарь для каждого ответа
        for submission in submissions:
            if submission.get('answers'):
                submission['answers'] = json.loads(submission['answers'])
        
        return submissions
    
    @staticmethod
    def update(submission_id, data):
        """Обновляет данные ответа на тест"""
        # Преобразуем ответы в JSON для хранения в базе данных
        if 'answers' in data and data['answers'] is not None:
            data['answers'] = json.dumps(data['answers'])
        
        response = supabase.table('submissions').update(data).eq('id', submission_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(submission_id):
        """Удаляет ответ на тест"""
        response = supabase.table('submissions').delete().eq('id', submission_id).execute()
        return True if response.data else False


class SupabaseGlossaryItem:
    """Адаптер для работы с элементами глоссария в Supabase"""
    
    @staticmethod
    def create(material_id, word, definition_ru, definition_uz, wrong_options=None):
        """Создает новый элемент глоссария"""
        item_id = str(uuid.uuid4())
        
        # Преобразуем неправильные варианты в JSON для хранения в базе данных
        wrong_options_json = json.dumps(wrong_options) if wrong_options else None
        
        item_data = {
            'id': item_id,
            'material_id': material_id,
            'word': word,
            'definition_ru': definition_ru,
            'definition_uz': definition_uz,
            'wrong_options': wrong_options_json,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('glossary_items').insert(item_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(item_id):
        """Получает элемент глоссария по ID"""
        response = supabase.table('glossary_items').select('*').eq('id', item_id).execute()
        if not response.data:
            return None
        
        item = response.data[0]
        
        # Преобразуем JSON обратно в список
        if item.get('wrong_options'):
            item['wrong_options'] = json.loads(item['wrong_options'])
        
        return item
    
    @staticmethod
    def get_by_material(material_id):
        """Получает все элементы глоссария для материала"""
        response = supabase.table('glossary_items').select('*').eq('material_id', material_id).execute()
        if not response.data:
            return []
        
        items = response.data
        
        # Преобразуем JSON обратно в список для каждого элемента
        for item in items:
            if item.get('wrong_options'):
                item['wrong_options'] = json.loads(item['wrong_options'])
        
        return items
    
    @staticmethod
    def update(item_id, data):
        """Обновляет данные элемента глоссария"""
        # Преобразуем неправильные варианты в JSON для хранения в базе данных
        if 'wrong_options' in data and data['wrong_options'] is not None:
            data['wrong_options'] = json.dumps(data['wrong_options'])
        
        response = supabase.table('glossary_items').update(data).eq('id', item_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(item_id):
        """Удаляет элемент глоссария"""
        response = supabase.table('glossary_items').delete().eq('id', item_id).execute()
        return True if response.data else False


class SupabaseChatConversation:
    """Адаптер для работы с чат-беседами в Supabase"""
    
    @staticmethod
    def create(title=None, is_group_chat=False):
        """Создает новую чат-беседу"""
        conversation_id = str(uuid.uuid4())
        
        conversation_data = {
            'id': conversation_id,
            'title': title,
            'is_group_chat': is_group_chat,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('chat_conversations').insert(conversation_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(conversation_id):
        """Получает чат-беседу по ID"""
        response = supabase.table('chat_conversations').select('*').eq('id', conversation_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_participant(user_id):
        """Получает все чат-беседы пользователя"""
        # Сначала получаем все ID бесед, в которых участвует пользователь
        participant_response = supabase.table('chat_participants').select('conversation_id').eq('user_id', user_id).execute()
        if not participant_response.data:
            return []
        
        conversation_ids = [item['conversation_id'] for item in participant_response.data]
        
        # Затем получаем сами беседы
        conversations = []
        for conversation_id in conversation_ids:
            conversation = SupabaseChatConversation.get_by_id(conversation_id)
            if conversation:
                conversations.append(conversation)
        
        return conversations
    
    @staticmethod
    def update(conversation_id, data):
        """Обновляет данные чат-беседы"""
        response = supabase.table('chat_conversations').update(data).eq('id', conversation_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(conversation_id):
        """Удаляет чат-беседу"""
        # Сначала удаляем всех участников
        supabase.table('chat_participants').delete().eq('conversation_id', conversation_id).execute()
        
        # Затем удаляем все сообщения
        supabase.table('chat_messages').delete().eq('conversation_id', conversation_id).execute()
        
        # Наконец, удаляем саму беседу
        response = supabase.table('chat_conversations').delete().eq('id', conversation_id).execute()
        return True if response.data else False


class SupabaseChatParticipant:
    """Адаптер для работы с участниками чат-бесед в Supabase"""
    
    @staticmethod
    def create(conversation_id, user_id, is_admin=False):
        """Добавляет участника в чат-беседу"""
        participant_data = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'is_admin': is_admin,
            'joined_at': datetime.utcnow().isoformat(),
            'last_read': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('chat_participants').insert(participant_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_conversation(conversation_id):
        """Получает всех участников чат-беседы"""
        response = supabase.table('chat_participants').select('*').eq('conversation_id', conversation_id).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update_last_read(conversation_id, user_id):
        """Обновляет время последнего прочтения сообщений"""
        data = {'last_read': datetime.utcnow().isoformat()}
        response = supabase.table('chat_participants').update(data).eq('conversation_id', conversation_id).eq('user_id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(conversation_id, user_id):
        """Удаляет участника из чат-беседы"""
        response = supabase.table('chat_participants').delete().eq('conversation_id', conversation_id).eq('user_id', user_id).execute()
        return True if response.data else False


class SupabaseChatMessage:
    """Адаптер для работы с сообщениями в чате в Supabase"""
    
    @staticmethod
    def create(conversation_id, sender_id, content, is_system_message=False, attachment_path=None):
        """Создает новое сообщение в чате"""
        message_id = str(uuid.uuid4())
        
        message_data = {
            'id': message_id,
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'content': content,
            'is_system_message': is_system_message,
            'attachment_path': attachment_path,
            'sent_at': datetime.utcnow().isoformat(),
        }
        
        response = supabase.table('chat_messages').insert(message_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_conversation(conversation_id, limit=50, offset=0):
        """Получает сообщения чат-беседы"""
        response = supabase.table('chat_messages').select('*').eq('conversation_id', conversation_id).order('sent_at', desc=True).limit(limit).offset(offset).execute()
        return response.data if response.data else []
    
    @staticmethod
    def delete(message_id):
        """Удаляет сообщение"""
        response = supabase.table('chat_messages').delete().eq('id', message_id).execute()
        return True if response.data else False
