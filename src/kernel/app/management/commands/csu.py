import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from kernel.utils import os_getenv

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates super user with custom username and password"

    def handle(self, *args, **options):
        email = os_getenv("SUPER_USER_EMAIL", "admin@admin.ru")
        if not User.objects.filter(email=email).exists():
            super_user = User(
                is_superuser=True,
                is_staff=True,
                email=email,
                username=os_getenv("SUPER_USER_NAME", "adm"),
            )
            super_user.set_password(os_getenv("SUPER_USER_PASSWORD", "123"))
            super_user.save()
            self.stdout.write(self.style.SUCCESS("Super user seed successful OK"))
            logger.info("Super user seed successful OK")
        else:
            self.stdout.write(self.style.SUCCESS("Super user already exists"))
