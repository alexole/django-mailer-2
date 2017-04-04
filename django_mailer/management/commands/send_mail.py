from django.core.management.base import BaseCommand
from django.db import connection
from django_mailer import models, settings
from django_mailer.engine import send_all
from django_mailer.management.commands import create_handler
import logging
import sys
try:
    from django.core.mail import get_connection
    EMAIL_BACKEND_SUPPORT = True
except ImportError:
    # Django version < 1.2
    EMAIL_BACKEND_SUPPORT = False


class Command(BaseCommand):
    help = 'Iterate the mail queue, attempting to send all mail.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--block-size', default=500, type=int,
            dest='block_size',
            help='The number of messages to iterate before checking the queue '
                 'again (in case new messages have been added while the queue '
                 'is being cleared).'
        )
        parser.add_argument(
            '--count', action='store_true', default=False,
            dest='count',
            help='Return the number of messages in the queue (without '
                 'actually sending any)'
        )

    def handle(self, *args, **options):
        count = options.get('count', None)
        block_size = options['block_size']
        verbosity = options['verbosity']

        # If this is just a count request the just calculate, report and exit.
        if count:
            queued = models.QueuedMessage.objects.non_deferred().count()
            deferred = models.QueuedMessage.objects.non_deferred().count()
            sys.stdout.write('%s queued message%s (and %s deferred message%s).'
                             '\n' % (queued, queued != 1 and 's' or '',
                                     deferred, deferred != 1 and 's' or ''))
            sys.exit()

        # Send logged messages to the console.
        logger = logging.getLogger('django_mailer')
        handler = create_handler(verbosity)
        logger.addHandler(handler)

        # if PAUSE_SEND is turned on don't do anything.
        if not settings.PAUSE_SEND:
            if EMAIL_BACKEND_SUPPORT:
                send_all(block_size, backend=settings.USE_BACKEND)
            else:
                send_all(block_size)
        else:
            logger = logging.getLogger('django_mailer.commands.send_mail')
            logger.warning("Sending is paused, exiting without sending "
                           "queued mail.")

        logger.removeHandler(handler)

        # Stop superfluous "unexpected EOF on client connection" errors in
        # Postgres log files caused by the database connection not being
        # explicitly closed.
        connection.close()
