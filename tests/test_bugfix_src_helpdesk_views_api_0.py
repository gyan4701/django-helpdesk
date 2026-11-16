from types import SimpleNamespace

from django.test import TestCase

from helpdesk import settings as helpdesk_settings
from helpdesk.views.api import TicketViewSet

from .helpers import create_ticket, get_user


class TicketStatusFilterByNameTest(TestCase):
    def test_filter_by_status_name_applies(self):
        """Requesting tickets by status name (e.g. ?status=Open) should return only tickets with that status."""
        # Find the numeric code for the human-readable status name 'Open'
        status_name = "Open"
        status_choices = helpdesk_settings.TICKET_STATUS_CHOICES
        try:
            open_code = next(code for code, name in status_choices if name == status_name)
        except StopIteration:
            self.skipTest("No 'Open' status in TICKET_STATUS_CHOICES")

        # Pick a different status code for another ticket (any that is not Open)
        other_code = next(code for code, name in status_choices if name != status_name)

        # Ensure there is at least one queue by creating tickets (create_ticket will create a queue if needed)
        t1 = create_ticket(status=open_code, title="Only Open ticket")
        t2 = create_ticket(status=other_code, title="Other status ticket")

        # Use a superuser/staff to avoid per-queue permission complications
        user = get_user(username="api.superuser", is_staff=True, is_superuser=True)

        # Create a fake request object with query_params supporting .get()
        request = SimpleNamespace(user=user, query_params={"status": status_name})

        view = TicketViewSet()
        view.request = request

        qs = view.get_queryset()

        # The bug causes the name-based filter to be ignored and both tickets returned.
        # Correct behaviour: only the ticket with status 'Open' should be returned.
        self.assertEqual(
            qs.count(),
            1,
            "Filtering by status name should return only tickets with that human-readable status",
        )
        only = qs.first()
        self.assertIsNotNone(only)
        self.assertEqual(
            only.status,
            open_code,
            "Returned ticket must have the numeric status code corresponding to the requested name",
        )
