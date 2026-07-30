---
document_id: integration-slack
title: Connecting SupportIQ Cloud to Slack
version: 1.0
last_updated: 2026-07-30
product_area: integrations
---

# Connecting SupportIQ Cloud to Slack

Slack is available on Starter, Growth, and Enterprise plans. Each connected
Slack workspace counts as one active external integration.

## Required permissions

The person connecting Slack must be:

- a SupportIQ organization administrator; and
- allowed to install applications in the target Slack workspace.

## Connection steps

1. Open **Administration > Integrations > Slack**.
2. Select **Connect workspace**.
3. Sign in to the target Slack workspace.
4. Review and approve the requested Slack permissions.
5. Return to SupportIQ and select the channel used for support notifications.
6. Send a test notification.

The connection is active only after the test notification succeeds.

## Data access

SupportIQ can post notifications to the selected channel and read interactions
with those notifications. It does not read unrelated channel history or direct
messages.

## Disconnecting

An organization administrator can disconnect Slack from the integration page.
Disconnecting stops new notifications immediately but does not delete existing
Slack messages.

If Slack access is revoked from Slack administration, SupportIQ displays the
integration as **Authorization required** until an administrator reconnects it.
