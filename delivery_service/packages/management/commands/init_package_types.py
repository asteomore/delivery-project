from django.core.management.base import BaseCommand

from packages.models import PackageType


class Command(BaseCommand):
    help = "Initialize package types"

    def handle(self, *args, **options):
        types = ["одежда", "электроника", "разное"]
        for type_name in types:
            PackageType.objects.get_or_create(name=type_name)
            self.stdout.write(self.style.SUCCESS(f"Created: {type_name}"))
