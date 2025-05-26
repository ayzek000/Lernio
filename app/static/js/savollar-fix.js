/**
 * savollar-fix.js - Скрипт для улучшения функциональности тестов
 * Включает функции для перемешивания вариантов ответов и корректного отображения результатов
 */

document.addEventListener('DOMContentLoaded', function() {
    // Перемешивание вариантов ответов при загрузке страницы
    shuffleTestOptions();
    
    // Исправление отображения результатов теста
    fixTestResults();
});

/**
 * Функция для перемешивания вариантов ответов в тестах
 * Перемешивает варианты ответов для каждого вопроса
 */
function shuffleTestOptions() {
    // Получаем все группы вопросов с вариантами ответов
    const questionGroups = document.querySelectorAll('.question-card .card-body .form-group');
    
    questionGroups.forEach(group => {
        // Проверяем, есть ли в группе радио-кнопки или чекбоксы (варианты ответов)
        const options = group.querySelectorAll('.form-check');
        if (options.length > 0) {
            // Получаем родительский элемент, содержащий все варианты
            const optionsContainer = options[0].parentElement;
            
            // Создаем массив из вариантов ответов
            const optionsArray = Array.from(options);
            
            // Перемешиваем массив
            for (let i = optionsArray.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                // Меняем местами элементы массива
                [optionsArray[i], optionsArray[j]] = [optionsArray[j], optionsArray[i]];
            }
            
            // Удаляем все варианты из контейнера
            while (optionsContainer.firstChild) {
                optionsContainer.removeChild(optionsContainer.firstChild);
            }
            
            // Добавляем перемешанные варианты обратно в контейнер
            optionsArray.forEach(option => {
                optionsContainer.appendChild(option);
            });
        }
    });
}

/**
 * Функция для исправления отображения результатов теста
 * Обеспечивает корректное отображение оценки в баллах и процентах
 */
function fixTestResults() {
    // Находим все элементы с оценками
    const scoreElements = document.querySelectorAll('.badge[class*="bg-"]');
    
    scoreElements.forEach(element => {
        const scoreText = element.textContent.trim();
        
        // Проверяем, содержит ли текст только процент
        if (scoreText.endsWith('%') && !scoreText.includes('/')) {
            // Извлекаем числовое значение процента
            const percentValue = parseFloat(scoreText);
            
            // Вычисляем значение в 10-балльной шкале
            const pointsValue = (percentValue / 10).toFixed(1);
            
            // Обновляем текст элемента
            element.textContent = `${pointsValue}/10 (${Math.round(percentValue)}%)`;
        }
    });
}