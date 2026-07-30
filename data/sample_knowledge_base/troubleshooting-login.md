---
document_id: troubleshooting-login
title: Troubleshooting Sign-In Problems
version: 1.0
last_updated: 2026-07-30
product_area: troubleshooting
---

# Troubleshooting Sign-In Problems

## Incorrect email or password

Users with password-based accounts should confirm their email address and use
the password-reset process after two unsuccessful attempts. Five unsuccessful
attempts within 15 minutes lock password sign-in for 15 minutes.

A password reset does not remove an active temporary lock. The user must wait
for the lock period to end.

## Single sign-on redirect loop

For an organization that requires single sign-on:

1. Confirm the user is launching SupportIQ from the correct organization URL.
2. Confirm the user's email domain is assigned to that organization.
3. Ask the organization administrator to verify the identity-provider
   assignment.
4. Clear SupportIQ and identity-provider browser cookies or retry in a private
   browser window.

Password reset does not resolve single sign-on errors.

## Browser requirements

SupportIQ supports the latest two stable versions of Chrome, Edge, Firefox, and
Safari. JavaScript and cookies must be enabled.

## Escalating to support

If the problem continues, provide:

- the approximate time of the failed sign-in;
- the organization name;
- whether password or single sign-on was used;
- the displayed error code;
- the browser and version.

Users must not send passwords, reset links, session cookies, or identity
provider secrets to support.
