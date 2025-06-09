#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функции перемешивания вариантов ответов
"""

import os
import sys
import json
import random
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_shuffle_function():
    """Тестируем логику перемешивания вариантов"""
    
    print("🧪 Тестируем логику перемешивания вариантов ответов...")
    
    # Пример данных вопроса как они создаются нашей системой
    original_options = {
        "A": "женская одежда",  # Правильный ответ
        "B": "детская одежда", 
        "C": "блуза",
        "D": "платье"
    }
    
    original_correct = "A"
    
    print(f"🔸 Исходные варианты: {original_options}")
    print(f"🔸 Правильный ответ: {original_correct} = '{original_options[original_correct]}'")
    
    # Симулируем функцию перемешивания
    def shuffle_options(options_dict, correct_key):
        # Получаем правильное значение
        correct_value = options_dict[correct_key]
        
        # Получаем все значения и перемешиваем их
        all_values = list(options_dict.values())
        random.shuffle(all_values)
        
        # Создаем новый словарь с новыми ключами
        new_options = {}
        for i, value in enumerate(all_values):
            key = chr(65 + i)  # A, B, C, D
            new_options[key] = value
        
        # Находим новый ключ для правильного ответа
        new_correct_key = None
        for key, value in new_options.items():
            if value == correct_value:
                new_correct_key = key
                break
        
        return new_options, new_correct_key
    
    # Тестируем несколько раз
    for i in range(5):
        new_options, new_correct_key = shuffle_options(original_options, original_correct)
        
        print(f"\n🔄 Попытка {i+1}:")
        print(f"   Новые варианты: {new_options}")
        print(f"   Новый правильный ответ: {new_correct_key} = '{new_options[new_correct_key]}'")
        
        # Проверяем что правильный ответ остался тем же значением
        if new_options[new_correct_key] == original_options[original_correct]:
            print("   ✅ Правильный ответ сохранен!")
        else:
            print("   ❌ Ошибка! Правильный ответ изменился!")
            return False
        
        # Проверяем что все варианты остались теми же, но в разном порядке
        original_values = set(original_options.values())
        new_values = set(new_options.values())
        
        if original_values == new_values:
            print("   ✅ Все варианты сохранены!")
        else:
            print("   ❌ Ошибка! Варианты ответов изменились!")
            return False
    
    print("\n🎉 Тест перемешивания прошел успешно!")
    return True

def test_json_format():
    """Тестируем формат JSON как в базе данных"""
    
    print("\n📋 Тестируем JSON формат...")
    
    # Пример как данные хранятся в базе
    options_json = '{"A": "женская одежда", "B": "детская одежда", "C": "блуза", "D": "платье"}'
    correct_json = '"A"'
    
    print(f"🔸 Options JSON: {options_json}")
    print(f"🔸 Correct JSON: {correct_json}")
    
    # Парсим JSON
    options_dict = json.loads(options_json)
    correct_answer = json.loads(correct_json)
    
    print(f"🔸 Parsed options: {options_dict}")
    print(f"🔸 Parsed correct: {correct_answer}")
    
    # Проверяем корректность
    if correct_answer in options_dict:
        print(f"✅ Правильный ответ '{correct_answer}' найден: '{options_dict[correct_answer]}'")
        return True
    else:
        print("❌ Ошибка! Правильный ответ не найден в вариантах!")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов функции перемешивания...\n")
    
    success1 = test_shuffle_function()
    success2 = test_json_format()
    
    if success1 and success2:
        print("\n🎊 Все тесты прошли успешно!")
        print("✨ Функция перемешивания должна работать корректно!")
    else:
        print("\n💥 Некоторые тесты провалились!")
        sys.exit(1)
