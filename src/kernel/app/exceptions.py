class NumberNotFound(ValueError):
    def __init__(self, num: str):
        super().__init__(f'Телефон "{num}" не найден в базе данных Россвязи')


class NumberNotRecognized(ValueError):
    def __init__(self, num: str):
        super().__init__(f'Телефон "{num}" не может быть распознан')
