from django.test import TestCase

from helpdesk import settings as helpdesk_settings
from helpdesk.models import Ticket
from helpdesk.views.api import TicketViewSet

from .helpers import create_ticket, get_staff_user


class SimpleRequest:
    def __init__(self, user, query_params):
        self.user = user
        # view.get_queryset only needs .get on query_params
        self.query_params = query_params


class StatusFilterByLabelTest(TestCase):
    def test_status_filter_accepts_status_label(self):
        """
        The API should accept human-readable status labels in the `status`
        query parameter (e.g. ?status=Open) and filter tickets accordingly.

        This exercises TicketViewSet.get_queryset which must map labels to the
        numeric choice keys before filtering. The bug caused the view to
        compare the query label to the numeric key (e.g. 'Open' == '1'), so no
        filter was applied and all tickets were returned.
        """
        # Pick two distinct status choices (label and numeric key)
        status_choices = helpdesk_settings.TICKET_STATUS_CHOICES
        assert len(status_choices) >= 2, "Need at least two status choices for this test"

        first_key, first_label = status_choices[0]
        second_key, second_label = status_choices[1]

        # Create two tickets with different numeric status values
        t1 = create_ticket(status=first_key)
        t2 = create_ticket(status=second_key)

        # Sanity check - they must be different statuses
        assert t1.status != t2.status

        # Prepare a view instance with a request that asks for the human label
        view = TicketViewSet()
        view.request = SimpleRequest(user=get_staff_user(), query_params={"status": first_label})

        qs = view.get_queryset()
        results = list(qs)

        # Correct behavior: only the ticket with the requested label's numeric
        # status should be returned.
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, t1.pk)
