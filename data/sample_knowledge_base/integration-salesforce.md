---
document_id: integration-salesforce
title: Connecting SupportIQ Cloud to Salesforce
version: 1.0
last_updated: 2026-07-30
product_area: integrations
---

# Connecting SupportIQ Cloud to Salesforce

The Salesforce integration is available only on Growth and Enterprise plans.
It synchronizes selected SupportIQ conversations with Salesforce cases.

## Requirements

The person completing setup must be:

- a SupportIQ organization administrator;
- a Salesforce administrator; and
- authorized to create a connected application in Salesforce.

The Salesforce account must permit API access.

## Connection steps

1. Open **Administration > Integrations > Salesforce**.
2. Select the Salesforce production or sandbox environment.
3. Sign in to Salesforce and approve API access.
4. Map the required SupportIQ fields to Salesforce case fields.
5. Select the synchronization direction.
6. Run **Validate mapping**.
7. Enable the integration after validation succeeds.

## Synchronization

New and updated records are normally synchronized within five minutes.
Deleting a record in one system does not delete the corresponding record in
the other system.

If a required field mapping is removed, synchronization pauses and SupportIQ
shows error code `SF-MAPPING-001`.

## Security

Salesforce credentials are authorized through OAuth. SupportIQ administrators
cannot view the Salesforce user's password.
