# Authentication Integration Guide

## Auth mechanism

The backend issues **JWT bearer tokens** returned in the JSON response body (NOT httpOnly cookies).

| Token | Lifetime | Purpose |
|-------|----------|---------|
| access_token | 30 minutes | Authorize API requests |
| refresh_token | 30 days | Obtain new access + refresh tokens (rotation) |

## Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/auth/register` | No | Create account, get tokens + user |
| POST | `/api/v1/auth/login` | No | Authenticate, get tokens + user |
| POST | `/api/v1/auth/refresh` | No (refresh token in body) | Rotate tokens |
| POST | `/api/v1/auth/logout` | No (refresh token in body) | Revoke refresh token |
| GET | `/api/v1/auth/me` | Yes (access token) | Get current user |

## Frontend token handling

Because tokens are in the response body (not cookies), the frontend must:

1. Store `access_token` and `refresh_token` after login/register.
2. Send `Authorization: Bearer <access_token>` on every protected request.
3. On `401` (expired access token), call `/auth/refresh` with the refresh token to get a new pair, then retry the original request.
4. If refresh also returns `401` (token reuse / revoked), clear all tokens and redirect to login.
5. On logout, call `/auth/logout` with the refresh token, then clear stored tokens.

**Security:** Do not store tokens in a way accessible to XSS if avoidable; prefer in-memory storage with session restore via refresh token, or httpOnly cookie middleware if the frontend framework supports it. The backend itself does not set httpOnly cookies, so the frontend is responsible for secure storage.

## Example login flow (pseudocode)

```ts
const res = await api.post("/auth/register", { email, full_name, password });
const { access_token, refresh_token, user } = res.data;
// store tokens
api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
```

## Protected-route behavior

- Any endpoint under `/api/v1/*` (except auth register/login and health) requires the access token.
- Missing/invalid/expired token → `401` with `detail` message.
- Do not expose stack traces or internals.

## Session expiry / refresh

Access token = 30 min. The frontend should proactively refresh before expiry or reactively on `401`. On refresh success, replace both tokens (rotation). On refresh failure, logout.

## Password policy (for registration form validation)

- min 12 chars
- require uppercase, lowercase, digit, special character

Validate these on the frontend to give immediate feedback before calling `/auth/register`.
