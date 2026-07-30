---
document_id: security-data-retention
title: Data Retention and Deletion
version: 1.0
last_updated: 2026-07-30
product_area: security
---

# Data Retention and Deletion

## Active subscriptions

Starter and Growth organizations retain conversation and knowledge-base data
for the lifetime of the active subscription.

Enterprise organizations can configure conversation retention from 30 to 365
days. Knowledge-base documents remain available until an authorized user
deletes them or the subscription ends.

Audit logs are retained for 12 months on Enterprise. Starter and Growth do not
include audit-log export.

## Deleted documents

When an authorized user deletes a knowledge-base document, it is removed from
search and new AI answers immediately. The document remains in recoverable
storage for 7 days, after which recovery is not available.

## Subscription termination

After a cancelled subscription's 30-day read-only period ends, SupportIQ
schedules the organization's customer content for deletion. Customer content
is deleted from active systems within 30 days.

Encrypted backup copies expire through normal backup rotation within 60 days
after deletion from active systems.

## Legal holds

SupportIQ may retain specific records longer when required by law or a valid
legal hold. Access to retained records is restricted to authorized legal and
security personnel.

## Export before deletion

Organization owners can export conversation and knowledge-base data during the
active subscription and the 30-day read-only period. Exports cannot be created
after access is disabled.
