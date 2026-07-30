---
document_id: account-email-change
title: Changing an Account Email Address
version: 1.0
last_updated: 2026-07-30
product_area: account
---

# Changing an Account Email Address

## Password-based accounts

A signed-in user with a password-based account can change their email address
from **Profile > Account settings > Email address**.

SupportIQ sends confirmation messages to both the old and new addresses. The
new address becomes active only after the user follows the verification link
sent to it. The verification link expires after 24 hours.

Changing the email address signs the user out of all active sessions except the
session used to confirm the change.

## Single sign-on accounts

Users managed through single sign-on cannot change their email address in
SupportIQ Cloud. An organization administrator must update the address in the
identity provider. SupportIQ synchronizes the new address at the user's next
successful sign-in.

## Lost access to the old address

Access to the old address is not required when the user is already signed in
and can verify the new address. If the user cannot sign in, an organization
administrator must submit the change from the administration console.

Support agents cannot change an account email address based only on an
unverified email request.
