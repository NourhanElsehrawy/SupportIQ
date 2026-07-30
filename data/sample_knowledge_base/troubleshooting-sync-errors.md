---
document_id: troubleshooting-sync-errors
title: Troubleshooting Integration Synchronization Errors
version: 1.0
last_updated: 2026-07-30
product_area: troubleshooting
---

# Troubleshooting Integration Synchronization Errors

## General checks

Before reconnecting an integration:

1. Check the SupportIQ status page for an active incident.
2. Confirm the external service is available.
3. Open **Administration > Integrations** and review the last successful sync.
4. Run **Retry failed records** once.

Repeated retries should not be used when an authorization or mapping error is
shown.

## Authorization errors

An integration marked **Authorization required** has an expired, revoked, or
insufficient authorization grant. An administrator must reconnect it. Existing
records remain available while synchronization is paused.

## Salesforce mapping error

Error `SF-MAPPING-001` means a required Salesforce field mapping is missing.
An administrator must restore the mapping and run **Validate mapping** before
resuming synchronization.

## Delayed records

Salesforce records normally synchronize within five minutes. A record should
be treated as delayed only after 15 minutes without an active incident.

Slack notifications normally arrive within one minute. If a Slack test
notification fails, confirm that the SupportIQ application is still installed
and permitted to post in the selected channel.

## Escalating to support

Provide the integration name, displayed error code, last successful sync time,
and affected record IDs. Do not send external-service passwords, OAuth tokens,
or API keys.
