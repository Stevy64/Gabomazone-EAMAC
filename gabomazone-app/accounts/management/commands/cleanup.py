from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Nettoie les sessions expirées et les données obsolètes'

    def handle(self, *args, **kwargs):
        from django.core.management import call_command
        call_command('clearsessions')
        self.stdout.write(self.style.SUCCESS('Sessions nettoyées.'))
