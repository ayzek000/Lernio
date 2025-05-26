// Глобальный JavaScript для сайта

// Настройка CSRF-защиты для AJAX-запросов
function setupCSRFProtection() {
    // Получаем CSRF-токен из мета-тега
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    if (csrfToken) {
        // Добавляем токен ко всем AJAX-запросам
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (!options.headers) {
                options.headers = {};
            }
            
            // Преобразуем заголовки в обычный объект, если они представлены в виде Headers
            if (options.headers instanceof Headers) {
                const originalHeaders = options.headers;
                options.headers = {};
                for (const [key, value] of originalHeaders.entries()) {
                    options.headers[key] = value;
                }
            }
            
            // Добавляем CSRF-токен в заголовки
            options.headers['X-CSRFToken'] = csrfToken;
            
            return originalFetch(url, options);
        };
        
        // Для XMLHttpRequest (устаревший способ AJAX)
        const originalXhrOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function() {
            const result = originalXhrOpen.apply(this, arguments);
            this.setRequestHeader('X-CSRFToken', csrfToken);
            return result;
        };
    } else {
        console.warn('CSRF токен не найден в мета-тегах. CSRF-защита не активирована.');
    }
}

// Вызываем функцию настройки CSRF-защиты
setupCSRFProtection();

document.addEventListener('DOMContentLoaded', function() {
    // Добавляем подтверждение для всех форм с атрибутом data-confirm
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const message = form.getAttribute('data-confirm') || 'Вы уверены, что хотите выполнить это действие?';
            if (!confirm(message)) {
                event.preventDefault(); // Отменить отправку, если пользователь нажал "Отмена"
            }
        });
    });

    // Инициализация всплывающих подсказок Bootstrap (если используются)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Добавление звездочки к обязательным полям форм (пример)
    const requiredInputs = document.querySelectorAll('input[required], textarea[required], select[required]');
    requiredInputs.forEach(input => {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label) {
            label.classList.add('required');
        }
    });

});

// Функция для динамического обновления choices в QuestionForm (пример для JS)
function updateCorrectAnswerChoices() {
    const typeSelect = document.getElementById('type'); // ID селектора типа вопроса
    const singleChoiceSelect = document.getElementById('correct_answer_single');
    const multipleChoiceSelect = document.getElementById('correct_answer_multiple'); // Это div или fieldset для чекбоксов

    if (!typeSelect || !singleChoiceSelect || !multipleChoiceSelect) return;

    // Собираем текущие варианты ответа
    const options = [
        { key: 'A', value: document.getElementById('option_a')?.value },
        { key: 'B', value: document.getElementById('option_b')?.value },
        { key: 'C', value: document.getElementById('option_c')?.value },
        { key: 'D', value: document.getElementById('option_d')?.value },
        { key: 'E', value: document.getElementById('option_e')?.value },
    ].filter(opt => opt.value && opt.value.trim() !== ''); // Только заполненные

    // Обновляем single choice select
    // Сохраняем выбранное значение
    const selectedSingle = singleChoiceSelect.value;
    singleChoiceSelect.innerHTML = '<option value="">---</option>'; // Очищаем и добавляем пустой
    options.forEach(opt => {
        const optionEl = document.createElement('option');
        optionEl.value = opt.key;
        optionEl.textContent = opt.key;
        singleChoiceSelect.appendChild(optionEl);
    });
    // Восстанавливаем выбор, если возможно
    singleChoiceSelect.value = selectedSingle;


    // Обновляем multiple choice (чекбоксы)
    // Сохраняем выбранные значения
    const selectedMultiple = Array.from(multipleChoiceSelect.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
    multipleChoiceSelect.innerHTML = ''; // Очищаем контейнер
    if (options.length > 0) {
        options.forEach(opt => {
            const div = document.createElement('div');
            div.className = 'form-check';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input';
            checkbox.name = 'correct_answer_multiple';
            checkbox.value = opt.key;
            checkbox.id = `correct_multi_${opt.key}`;
             // Восстанавливаем выбор
            if (selectedMultiple.includes(opt.key)) {
                checkbox.checked = true;
            }
            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.htmlFor = checkbox.id;
            label.textContent = opt.key;
            div.appendChild(checkbox);
            div.appendChild(label);
            multipleChoiceSelect.appendChild(div);
        });
    } else {
        multipleChoiceSelect.innerHTML = '<p class="text-muted small">Заполните варианты ответов</p>';
    }


    // Показываем/скрываем нужные поля в зависимости от типа вопроса
    const singleGroup = singleChoiceSelect.closest('.mb-3'); // Найти родительский div
    const multipleGroup = multipleChoiceSelect.closest('.mb-3');

    if (typeSelect.value === 'single_choice') {
        if (singleGroup) singleGroup.style.display = 'block';
        if (multipleGroup) multipleGroup.style.display = 'none';
    } else if (typeSelect.value === 'multiple_choice') {
        if (singleGroup) singleGroup.style.display = 'none';
        if (multipleGroup) multipleGroup.style.display = 'block';
    } else {
        if (singleGroup) singleGroup.style.display = 'none';
        if (multipleGroup) multipleGroup.style.display = 'none';
    }
}

// Вызываем функцию при загрузке и при изменении полей вариантов или типа
document.addEventListener('DOMContentLoaded', () => {
    const questionForm = document.querySelector('#questionForm'); // Дать ID форме вопроса
    if (questionForm) {
        updateCorrectAnswerChoices(); // Вызов при загрузке
        questionForm.addEventListener('input', updateCorrectAnswerChoices); // Вызов при вводе в полях
        questionForm.addEventListener('change', updateCorrectAnswerChoices); // Вызов при изменении select
    }
});