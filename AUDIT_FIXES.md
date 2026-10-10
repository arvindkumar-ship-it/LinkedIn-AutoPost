# Owner access and atomic local storage

Repair branch: `fix/internship-audit-20261010`. Changes are scoped to audit findings; no deployment or live provider action is included.

## Changed

Added a server-configured owner access token and signed expiring cookie; OAuth state is validated and callbacks/errors avoid exposing raw tokens. Local JSON updates use locking and atomic replacement; regression tests cover concurrent writes and invalid sessions.

## Verification

`pytest -q`

Commands are entry points, not a claim that every live integration was executed. See the repair bundle for actual results.

## Setup and remaining evidence

Set APP_ACCESS_TOKEN to 32+ random characters and configure OAuth credentials and callback URL in the backend environment. Keep app access credentials out of Git. This is a single-owner local deployment, not multi-user OAuth account storage. Token encryption/key management, a durable distributed scheduler and actual LinkedIn-approved scope/publishing checks remain open. No posts or messages were sent during this repair.
