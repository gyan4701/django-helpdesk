from django.test import TestCase
from django.conf import settings

from helpdesk.forms import PublicTicketForm
from helpdesk.models import Ticket, Queue

from .helpers import get_user, create_ticket


class TestPublicTicketFormMissingConfiguredQueue(TestCase):
    def setUp(self):
        # Ensure the test slug does not exist
        Queue.objects.filter(slug="no-default").delete()

    def test_save_handles_missing_configured_queue(self):
        """When HELPDESK_PUBLIC_TICKET_QUEUE points to a non-existent slug, save() should not raise an AttributeError and should return the ticket."""
        # Preserve original setting and replace with a slug that does not exist
        original = getattr(settings, "HELPDESK_PUBLIC_TICKET_QUEUE", None)
        settings.HELPDESK_PUBLIC_TICKET_QUEUE = "no-default"

        try:
            # Create a real Ticket instance to be returned by the form's _create_ticket
            ticket = create_ticket()

            form = PublicTicketForm()

            # Patch the instance methods used by save() so we can focus on the bug in save()
            # _create_ticket should return (ticket, None) to simulate _get_queue returning None
            form._create_ticket = lambda: (ticket, None)
            # prevent side-effects from other helpers called by save()
            form._create_custom_fields = lambda t: None

            class _FU:
                def save(self):
                    return None

            form._create_follow_up = lambda ticket, title, user: _FU()
            form._attach_files_to_follow_up = lambda followup: []
            form._send_messages = lambda **kwargs: None

            user = get_user()

            # The bug manifested as an AttributeError from accessing queue.default_owner when queue is None.
            # The correct behaviour is that save() should not raise in this situation.
            result = form.save(user)

            # It should return the Ticket instance we provided
            self.assertIsInstance(result, Ticket)
            self.assertEqual(result.pk, ticket.pk)

            # Since there was no queue, ticket.assigned_to should remain unset (None)
            self.assertIsNone(result.assigned_to)

        finally:
            # Restore original setting
            if original is None:
                if hasattr(settings, "HELPDESK_PUBLIC_TICKET_QUEUE"):
                    delattr(settings, "HELPDESK_PUBLIC_TICKET_QUEUE")
            else:
                settings.HELPDESK_PUBLIC_TICKET_QUEUE = original
