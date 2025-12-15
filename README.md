# AtraksTrade


Для запуска проекта необходимо выполнить следующие шаги:
Установить утилиты Make и Docker на вашу систему.

make help - показать доступные команды Makefile.
![Вывод команды make help](assets/images/img.png)


make env - Для .env файла.
make up - Запустить контейнеры Docker.
make update_rossvyaz - Получить данные Россвязи.

Далее можно будет командой docker ps посмотреть запущенные контейнеры.
![Запуск всех контейнеров](assets/images/img.png)

По адресу http://localhost:8000/ будет доступен сам проект.
![Главная страница](assets/images/img_2.png)

Введите номер и нажмите кнопку "Проверить".
![Получение данных](assets/images/img_3.png)

По адресу http://localhost:8000/api/docs/ будет доступна документация по API проекта.
![Документация по API](assets/images/img_5.png)

После запуска можно будет перейти в админ панель с паролем admin и логином admin по адресу http://localhost:8000/admin.
![](assets/images/img_4.png)