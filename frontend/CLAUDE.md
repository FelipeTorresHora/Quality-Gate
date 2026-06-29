# CLAUDE.md (frontend)

Scope: `frontend/`. Read root `CLAUDE.md` first for cross-cutting architecture.

## Commands

```bash
npm run dev       # vite dev server, port 5173
npm run build     # tsc -b && vite build (type errors fail the build)
npm run preview
```

No test runner, no eslint config in this package — `tsc` is the only check (also runs via `npm run build`). No path aliases configured in `tsconfig.json`; imports are relative (`../api/client`, `../types/api`).

## Conventions

- Every API call goes through `src/api/client.ts`'s `request<T>` helper. Add a new exported function there for each endpoint — don't `fetch` directly in a page/component.
- `ApiError` (status + `{code, message}`) is the only error shape thrown by the client; pages catch it into local `error` state and render it with `<ErrorMessage error={...} />`. Follow that pattern, don't add a toast/global error system.
- DTOs live in `src/types/api.ts` and must mirror the backend Pydantic schemas field-for-field (snake_case keys, matching optionality) — when a backend schema changes, update this file in the same change.
- No state/query library (no React Query, no Redux/Zustand) — pages fetch in a plain `useEffect` + `useState` and re-fetch manually after mutations (see `RepositoryDetailPage.tsx`). Stay consistent with this until a library is explicitly introduced.
- Routing is centralized in `App.tsx`; add new routes there, one page per route under `src/pages/`.
- Styling is one global stylesheet, `src/styles/app.css`, using plain class names (`page-stack`, `panel`, `button primary`, etc.) — no CSS modules, no Tailwind, no styled-components. Reuse existing classes before adding new ones.
- Small, purely presentational pieces (status pills, error boxes) go in `src/components/`; anything that fetches data or owns route-level state is a page, not a component.

## Gotchas

- `VITE_API_BASE_URL` defaults to `http://localhost:8000` in `client.ts` if unset — Docker Compose passes it explicitly as a build/runtime env var.
- `request<T>` sends `credentials: "include"` because authentication uses an HttpOnly dashboard session cookie.
- `AuthGate` owns the unauthenticated login state. Product pages should assume an authenticated user and must not add manual repository or mock-analysis controls.
