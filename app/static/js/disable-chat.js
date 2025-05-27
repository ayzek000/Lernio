// Скрипт для отключения функциональности чата
document.addEventListener('DOMContentLoaded', function() {
    // Перехватываем все AJAX-запросы
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Если запрос связан с чатом или сообщениями, блокируем его
        if (typeof url === 'string' && (
            url.includes('/chat') || 
            url.includes('/message') || 
            url.includes('chat_') || 
            url.includes('message_')
        )) {
            console.log('Запрос к API чата заблокирован:', url);
            // Возвращаем пустой успешный ответ вместо реального запроса
            return Promise.resolve(new Response(JSON.stringify({
                success: true,
                data: [],
                message: 'Функция отправки сообщений временно отключена'
            }), {
                status: 200,
                headers: {
                    'Content-Type': 'application/json'
                }
            }));
        }
        
        // Для всех остальных запросов используем оригинальный fetch
        return originalFetch(url, options);
    };
    
    // Также перехватываем XMLHttpRequest для старых скриптов
    const originalXhrOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        if (typeof url === 'string' && (
            url.includes('/chat') || 
            url.includes('/message') || 
            url.includes('chat_') || 
            url.includes('message_')
        )) {
            console.log('XMLHttpRequest к API чата заблокирован:', url);
            // Изменяем URL на несуществующий, чтобы запрос не прошел
            url = '/disabled-chat-api';
        }
        return originalXhrOpen.call(this, method, url, ...args);
    };
    
    console.log('Функциональность чата временно отключена');
});
