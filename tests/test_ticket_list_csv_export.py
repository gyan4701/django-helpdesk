from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from helpdesk.models import Queue, Ticket
from helpdesk.query import query_to_base64

User = get_user_model()


class TicketListCSVExportTests(TestCase):
    """
    Tests for CSV export of the staff ticket list.
    """

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staffuser1", password="testpass123", is_staff=True
        )
        self.queue = Queue.objects.create(title="Payments", slug="payments")
        self.ticket = Ticket.objects.create(
            title="My card got double charged!",
            submitter_email="customer@example.com",
            queue=self.queue,
        )
        self.url = reverse("helpdesk:list")
        self.default_params = {
            "filtering": {"status__in": [1, 2]},
            "sorting": "created",
            "search_string": "",
            "sortreverse": False,
        }
        self.encoded_query = query_to_base64(self.default_params)

    def test_requesting_list_with_export_csv_returns_csv_and_attachment_and_contains_ticket(
        self,
    ):
        # Arrange
        self.client.force_login(self.staff_user)

        # Act
        r = self.client.get(self.url, data={"qs": self.encoded_query, "export": "csv"})

        # Assert: status and content type
        self.assertEqual(r.status_code, HTTPStatus.OK)
        # Content-Type may include charset; ensure text/csv present
        self.assertIn("text/csv", r["Content-Type"])

        # Content-Disposition should indicate attachment filename
        content_disposition = r.get("Content-Disposition", "")
        self.assertTrue(content_disposition)
        self.assertIn("attachment", content_disposition)
        self.assertIn("filename", content_disposition)

        # Decode CSV and check header row has eight columns
        content = r.content.decode("utf-8", errors="replace").splitlines()
        self.assertTrue(len(content) >= 1)
        header = content[0]
        # Split on commas to count columns (basic verification)
        header_cols = [c for c in header.split(",")]
        self.assertEqual(len(header_cols), 8)

        # Check that our ticket appears in the CSV body
        body_rows = content[1:]
        joined_body = "\n".join(body_rows)
        self.assertIn(self.ticket.title, joined_body)
        self.assertIn(self.ticket.submitter_email, joined_body)
        self.assertIn(self.queue.title, joined_body)

    def test_requesting_without_export_renders_html_template(self):
        # Arrange
        self.client.force_login(self.staff_user)

        # Act
        r = self.client.get(self.url, data={"qs": self.encoded_query})

        # Assert
        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(r, "helpdesk/ticket_list.html")
        # Ensure HTML content type
        self.assertIn("text/html", r["Content-Type"])
