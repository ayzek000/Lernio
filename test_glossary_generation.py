#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генерации тестов из словаря
"""

import os
import sys
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Lesson, GlossaryItem, Material, Test, Question

def test_glossary_generation():
    """Тестируем генерацию тестов из словаря"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Начинаем тестирование генерации тестов из словаря...")
        
        # Проверяем есть ли уроки
        lessons = Lesson.query.all()
        if not lessons:
            print("❌ Нет уроков в базе данных")
            return False
            
        lesson = lessons[0]
        print(f"✅ Используем урок: {lesson.title}")
        
        # Проверяем есть ли материал словаря
        glossary_material = Material.query.filter_by(lesson_id=lesson.id, type='glossary').first()
        
        if not glossary_material:
            print("📚 Создаем материал словаря...")
            glossary_material = Material(
                lesson_id=lesson.id,
                title=f"Тестовый словарь для урока: {lesson.title}",
                type='glossary',
                content="Автоматически созданный словарь для тестирования"
            )
            db.session.add(glossary_material)
            db.session.commit()
            print("✅ Материал словаря создан")
        else:
            print(f"✅ Найден материал словаря: {glossary_material.title}")
        
        # Проверяем есть ли элементы словаря
        glossary_items = GlossaryItem.query.filter_by(material_id=glossary_material.id).all()
        
        if not glossary_items:
            print("📝 Создаем тестовые элементы словаря...")
            
            test_terms = [
                {
                    'word': 'ayollar kiyimlari',
                    'definition_ru': 'женская одежда',
                    'definition_uz': "women's clothing"
                },
                {
                    'word': 'ayollar ko\'ylagi', 
                    'definition_ru': 'платье',
                    'definition_uz': 'dress'
                },
                {
                    'word': 'bichim',
                    'definition_ru': 'крой, форма',
                    'definition_uz': 'cut, shape'
                },
                {
                    'word': 'bluzka',
                    'definition_ru': 'блуза',
                    'definition_uz': 'blouse'
                },
                {
                    'word': 'bolalar kiyimlari',
                    'definition_ru': 'детская одежда',
                    'definition_uz': "children's clothing"
                }
            ]
            
            for term_data in test_terms:
                glossary_item = GlossaryItem(
                    material_id=glossary_material.id,
                    word=term_data['word'],
                    definition_ru=term_data['definition_ru'],
                    definition_uz=term_data['definition_uz']
                )
                db.session.add(glossary_item)
            
            db.session.commit()
            glossary_items = GlossaryItem.query.filter_by(material_id=glossary_material.id).all()
            print(f"✅ Создано {len(glossary_items)} элементов словаря")
        else:
            print(f"✅ Найдено {len(glossary_items)} элементов словаря")
        
        # Тестируем генерацию теста для русского языка
        print("\n🧪 Тестируем генерацию теста: узбекский → русский")
        
        # Создаем тест
        test_title = f"Rus tili bo'yicha lug'at testi: {lesson.title}"
        new_test = Test(
            lesson_id=lesson.id,
            title=test_title,
            description=f'Avtomatik yaratilgan lug\'at testi: {lesson.title}'
        )
        db.session.add(new_test)
        db.session.flush()
        
        questions_created = 0
        
        # Создаем вопросы
        for item in glossary_items:
            if item.definition_ru:
                question = Question(
                    test_id=new_test.id,
                    text=f'Quyidagi atama uchun rus tilidagi tarjimani tanlang: "{item.word}"',
                    type='single_choice'
                )
                
                # Получаем неправильные варианты ответов из других терминов
                wrong_options = []
                other_items = GlossaryItem.query.filter(
                    GlossaryItem.id != item.id,
                    GlossaryItem.definition_ru.isnot(None)
                ).limit(3).all()
                
                for other_item in other_items:
                    if other_item.definition_ru and other_item.definition_ru != item.definition_ru:
                        wrong_options.append(other_item.definition_ru)
                
                # Формируем варианты ответов
                options = [item.definition_ru] + wrong_options[:3]
                
                # Создаем словарь вариантов с ключами A, B, C, D
                options_dict = {}
                correct_key = None
                for i, option in enumerate(options):
                    key = chr(65 + i)  # A, B, C, D
                    options_dict[key] = option
                    if option == item.definition_ru:
                        correct_key = key
                
                question.options = json.dumps(options_dict, ensure_ascii=False)
                question.correct_answer = json.dumps(correct_key)
                db.session.add(question)
                questions_created += 1
        
        db.session.commit()
        
        if questions_created > 0:
            print(f"✅ Тест '{test_title}' успешно создан с {questions_created} вопросами")
            
            # Показываем примеры вопросов
            questions = Question.query.filter_by(test_id=new_test.id).limit(2).all()
            print("\n📋 Примеры созданных вопросов:")
            
            for i, q in enumerate(questions, 1):
                print(f"\n{i}. {q.text}")
                options = json.loads(q.options)
                correct = json.loads(q.correct_answer)
                
                for key, value in options.items():
                    marker = "✓" if key == correct else " "
                    print(f"   {key}) {value} {marker}")
            
            return True
        else:
            print("❌ Не удалось создать вопросы")
            return False

if __name__ == "__main__":
    success = test_glossary_generation()
    if success:
        print("\n🎉 Тестирование завершено успешно!")
    else:
        print("\n💥 Тестирование провалено!")
        sys.exit(1)
