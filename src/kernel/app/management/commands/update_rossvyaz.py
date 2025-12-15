from django.core.management.base import BaseCommand

from app.services import update_info


class Command(BaseCommand):
    help = "Обновление данных реестра нумерации (диапазоны номеров, операторы, регионы)"

    def handle(self, *args, **options):
        self.stdout.write("Запуск обновления данных...")
        update_info()
        self.stdout.write(self.style.SUCCESS("Обновление закончено"))
