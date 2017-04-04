from django.core.management.base import BaseCommand
from django_mailer import models
from django_mailer.management.commands import create_handler
import logging


class Command(BaseCommand):
    help = 'Place deferred messages back in the queue.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries', type=int,
            dest='max_retries',
            help='The number of messages to iterate before checking the queue '
                 'again (in case new messages have been added while the queue '
                 'is being cleared).'
        )

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        max_retries = options.get('max_retries')
        # Send logged messages to the console.
        logger = logging.getLogger('django_mailer')
        handler = create_handler(verbosity)
        logger.addHandler(handler)

        count = models.QueuedMessage.objects.retry_deferred(
                                                    max_retries=max_retries)
        logger = logging.getLogger('django_mailer.commands.retry_deferred')
        logger.warning("%s deferred message%s placed back in the queue" %
                       (count, count != 1 and 's' or ''))

        logger.removeHandler(handler)
