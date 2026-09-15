def validate_scopes(scopes: set) -> bool:
    """Сверяет указанные scopes с актуальным списком.
    
    Возвращает True при успешной валидации
    
    При ошибке валидации возвращает ``InvalidScopeError`` с неверными scopes"""