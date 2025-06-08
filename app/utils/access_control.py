from flask_login import current_user

def check_user_access(user, content_type, content_id):
    """
    Проверяет, имеет ли пользователь доступ к указанному контенту.
    
    Args:
        user: Объект пользователя
        content_type: Тип контента ('lesson', 'material', 'test')
        content_id: ID контента
        
    Returns:
        bool: True, если доступ разрешен, False в противном случае
    """
    # Если пользователь - учитель или админ, у него всегда есть доступ
    if user.is_teacher or user.is_admin:
        return True
        
    # По умолчанию все студенты имеют доступ ко всему контенту
    # В будущем здесь можно реализовать проверку по группам, если они будут добавлены
    try:
        # Если в будущем будет добавлена поддержка групп, раскомментируйте этот код
        # if hasattr(user, 'group_id') and user.group_id:
        #     from app.models_group import check_group_access
        #     return check_group_access(user.group_id, content_type, content_id)
        return True
    except Exception as e:
        # В случае ошибки разрешаем доступ по умолчанию
        import logging
        logging.error(f"Ошибка при проверке доступа: {str(e)}")
        return True

def filter_content_by_access(user, content_list, content_type):
    """
    Фильтрует список контента на основе прав доступа пользователя.
    
    Args:
        user: Объект пользователя
        content_list: Список объектов контента (уроки, материалы, тесты)
        content_type: Тип контента ('lesson', 'material', 'test')
        
    Returns:
        list: Отфильтрованный список контента, к которому у пользователя есть доступ
    """
    # Если пользователь - учитель или админ, возвращаем весь список
    if user.is_teacher or user.is_admin:
        return content_list
    
    # В текущей реализации все студенты имеют доступ ко всему контенту
    # В будущем здесь можно реализовать фильтрацию по группам
    
    # Раскомментируйте этот код, если в будущем будет добавлена поддержка групп
    # if hasattr(user, 'group_id') and user.group_id:
    #     return [item for item in content_list if check_user_access(user, content_type, item.id)]
    
    # По умолчанию возвращаем весь список
    return content_list
