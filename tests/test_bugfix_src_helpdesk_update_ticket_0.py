from django.test import TestCase
from django.core.exceptions import ValidationError

from helpdesk.update_ticket import subscribe_to_ticket_updates

from .helpers import create_ticket


class TestSubscribeToTicketUpdates(TestCase):
    def setUp(self):
        self.ticket = create_ticket()

    def test_missing_user_and_email_raises_validation_error(self):
        """Calling subscribe_to_ticket_updates with neither user_id nor email should raise ValidationError, not TypeError."""
        with self.assertRaises(ValidationError):
            # Call with defaults (user_id=None, email=None)
            subscribe_to_ticket_updates(self.ticket)
