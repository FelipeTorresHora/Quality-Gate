# Use HTTP-Only Session Cookies

Accepted on 2026-06-23. GitHub OAuth Login will create a local dashboard session stored in an HTTP-only cookie instead of exposing bearer tokens to the frontend. This keeps browser-side authentication simple and avoids persisting GitHub or dashboard tokens in client-side JavaScript.
