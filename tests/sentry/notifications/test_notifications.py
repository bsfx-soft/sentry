import logging
import uuid
from time import time
from urllib.parse import parse_qs

import responses
from django.core import mail
from django.utils import timezone

from sentry.event_manager import EventManager
from sentry.models import ExternalActor, Group, GroupAssignee, GroupStatus, Integration, UserOption
from sentry.testutils import APITestCase
from sentry.types.integrations import ExternalProviders
from sentry.utils import json


def make_event(**kwargs):
    result = {
        "event_id": uuid.uuid1().hex,
        "level": logging.ERROR,
        "logger": "default",
        "tags": [],
    }
    result.update(kwargs)
    return result


def get_attachment():
    assert len(responses.calls) >= 1
    data = parse_qs(responses.calls[0].request.body)
    assert "attachments" in data
    attachments = json.loads(data["attachments"][0])

    assert len(attachments) == 1
    return attachments[0]


class ActivityNotificationTest(APITestCase):
    """
    Enable Slack AND email notification settings for a user
    """

    def setUp(self):
        super().setUp()
        self.integration = Integration.objects.create(
            provider="slack",
            name="Team A",
            external_id="TXXXXXXX1",
            metadata={
                "access_token": "xoxp-xxxxxxxxx-xxxxxxxxxx-xxxxxxxxxxxx",
                "installation_type": "born_as_bot",
            },
        )
        self.integration.add_organization(self.organization, self.user)
        ExternalActor.objects.create(
            actor=self.user.actor,
            organization=self.organization,
            integration=self.integration,
            provider=ExternalProviders.SLACK.value,
            external_name="hellboy",
            external_id="UXXXXXXX1",
        )
        UserOption.objects.create(user=self.user, key="self_notifications", value="1")
        url = f"/api/0/users/{self.user.id}/notification-settings/"
        data = {
            "workflow": {"user": {self.user.id: {"email": "always", "slack": "always"}}},
            "deploy": {"user": {self.user.id: {"email": "always", "slack": "always"}}},
            "alerts": {"user": {self.user.id: {"email": "always", "slack": "always"}}},
        }
        self.login_as(self.user)
        with self.feature("organizations:notification-platform"):
            response = self.client.put(url, format="json", data=data)
        assert response.status_code == 204, response.content

        responses.add(
            method=responses.POST,
            url="https://slack.com/api/chat.postMessage",
            body='{"ok": true}',
            status=200,
            content_type="application/json",
        )
        self.name = self.user.get_display_name()
        self.short_id = self.group.qualified_short_id

    @responses.activate
    def test_sends_note_notification(self):
        """
        Test that an email AND Slack notification are sent with
        the expected values when a comment is created on an issue.
        """

        # leave a comment
        url = f"/api/0/issues/{self.group.id}/comments/"
        with self.tasks():
            response = self.client.post(url, format="json", data={"text": "blah blah"})
        assert response.status_code == 201, response.content

        msg = mail.outbox[0]
        # check the txt version
        assert "blah blah" in msg.body
        # check the html version
        assert "blah blah</p></div>" in msg.alternatives[0][0]

        attachment = get_attachment()
        # check the Slack version
        assert attachment["title"] == f"New comment by {self.name}"
        assert attachment["text"] == "blah blah"
        assert (
            attachment["footer"]
            == f"<http://testserver/organizations/{self.organization.slug}/issues/{self.group.id}/?referrer=NoteActivitySlack|{self.short_id}> via <http://testserver/settings/account/notifications/?referrer=NoteActivitySlack|Notification Settings>"
        )

    @responses.activate
    def test_sends_assignment_notification(self):
        """
        Test that an email AND Slack notification are sent with
        the expected values when an issue is assigned.
        """

        # assign the issue
        url = f"/api/0/issues/{self.group.id}/"

        with self.tasks():
            response = self.client.put(url, format="json", data={"assignedTo": self.user.username})
        assert response.status_code == 200, response.content

        msg = mail.outbox[0]
        # check the txt version
        assert f"assigned {self.short_id} to themselves" in msg.body
        # check the html version
        assert f"{self.short_id}</a> to themselves</p>" in msg.alternatives[0][0]

        attachment = get_attachment()

        assert attachment["title"] == "Assigned"
        assert attachment["text"] == f"{self.name} assigned {self.short_id} to themselves"
        assert (
            attachment["footer"]
            == f"<http://testserver/organizations/{self.organization.slug}/issues/{self.group.id}/?referrer=AssignedActivitySlack|{self.short_id}> via <http://testserver/settings/account/notifications/?referrer=AssignedActivitySlack|Notification Settings>"
        )

    @responses.activate
    def test_sends_unassignment_notification(self):
        """
        Test that an email AND Slack notification are sent with
        the expected values when an issue is unassigned.
        """
        # assign the issue
        url = f"/api/0/issues/{self.group.id}/"
        GroupAssignee.objects.create(
            group=self.group, project=self.project, user=self.user, date_added=timezone.now()
        )
        with self.tasks():
            response = self.client.put(url, format="json", data={"assignedTo": ""})
        assert response.status_code == 200, response.content

        msg = mail.outbox[0]
        # check the txt version
        assert f"Unassigned\n\n{self.user.username} unassigned {self.short_id}" in msg.body
        # check the html version
        assert f"{self.user.username}</strong> unassigned" in msg.alternatives[0][0]

        attachment = get_attachment()

        assert attachment["title"] == "Unassigned"
        assert attachment["text"] == f"{self.name} unassigned {self.short_id}"
        assert (
            attachment["footer"]
            == f"<http://testserver/organizations/{self.organization.slug}/issues/{self.group.id}/?referrer=UnassignedActivitySlack|{self.short_id}> via <http://testserver/settings/account/notifications/?referrer=UnassignedActivitySlack|Notification Settings>"
        )

    @responses.activate
    def test_sends_resolution_notification(self):
        """
        Test that an email AND Slack notification are sent with
        the expected values when an issue is resolved.
        """
        # resolve the issue
        url = f"/api/0/issues/{self.group.id}/"
        with self.tasks():
            response = self.client.put(url, format="json", data={"status": "resolved"})
        assert response.status_code == 200, response.content

        msg = mail.outbox[0]
        # check the txt version
        assert f"{self.user.username} marked {self.short_id} as resolved" in msg.body
        # check the html version
        assert f"{self.short_id}</a> as resolved</p>" in msg.alternatives[0][0]

        attachment = get_attachment()

        assert attachment["title"] == "Resolved Issue"
        assert attachment["text"] == f"{self.name} marked {self.short_id} as resolved"
        assert (
            attachment["footer"]
            == f"<http://testserver/organizations/{self.organization.slug}/issues/{self.group.id}/?referrer=ResolvedActivitySlack|{self.short_id}> via <http://testserver/settings/account/notifications/?referrer=ResolvedActivitySlack|Notification Settings>"
        )

    @responses.activate
    def test_sends_regression_notification(self):
        """
        Test that an email AND Slack notification are sent with
        the expected values when an issue regresses.
        """
        # resolve and unresolve the issue
        ts = time() - 300
        manager = EventManager(make_event(event_id="a" * 32, checksum="a" * 32, timestamp=ts))
        with self.tasks():
            event = manager.save(self.project.id)

        group = Group.objects.get(id=event.group_id)
        group.status = GroupStatus.RESOLVED
        group.save()
        assert group.is_resolved()

        manager = EventManager(make_event(event_id="b" * 32, checksum="a" * 32, timestamp=ts + 50))
        with self.tasks():
            event2 = manager.save(self.project.id)
        assert event.group_id == event2.group_id

        group = Group.objects.get(id=group.id)
        assert not group.is_resolved()

        msg = mail.outbox[0]
        # check the txt version
        assert f"Sentry marked {group.qualified_short_id} as a regression" in msg.body
        # check the html version
        assert f"{group.qualified_short_id}</a> as a regression</p>" in msg.alternatives[0][0]

        attachment = get_attachment()

        assert attachment["title"] == "Regression"
        assert attachment["text"] == f"Sentry marked {group.qualified_short_id} as a regression"
        assert (
            attachment["footer"]
            == f"<http://testserver/organizations/{self.organization.slug}/issues/{group.id}/?referrer=RegressionActivitySlack|{group.qualified_short_id}> via <http://testserver/settings/account/notifications/?referrer=RegressionActivitySlack|Notification Settings>"
        )

    @responses.activate
    def test_sends_processing_issue_notification(self):
        pass

    @responses.activate
    def test_sends_resolved_in_release_notification(self):
        pass

    @responses.activate
    def test_sends_deployment_notification(self):
        pass

    @responses.activate
    def test_sends_issue_notification(self):
        pass
