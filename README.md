# Ziloo AI — frontend

A React + TypeScript + Tailwind frontend for the MyAI backend (FastAPI +
GLM-5.2/Kimi K3 routing). Vite-powered, no framework beyond React itself.

## Quickstart

```bash
npm install
npm run dev
```

Opens on `http://localhost:5173`. By default it talks to a backend at
`http://localhost:8000` — change this by opening the browser console and running:

```js
localStorage.setItem("ziloo:apiBaseUrl", "https://your-cloud-run-url")
```

(See `src/lib/api.ts` — the base URL is read from `localStorage` rather than
baked in at build time, so the same build works against local Docker or a
deployed Cloud Run backend without a rebuild.)

## Design decisions

**Colors and type.** Same dual-accent system as the plain-JS version this
replaced: teal for GLM-5.2, amber for Kimi K3, on a dark charcoal base.
Space Grotesk for display text, IBM Plex Sans for body, IBM Plex Mono for
anything code/ID-shaped. All defined in `tailwind.config.ts`.

**The signature idea carries through the redesign.** The one deliberate,
non-decorative element is still that every assistant message shows *which
model answered it*, via a colored left border and a badge
(`src/components/chat/MessageBubble.tsx`, `src/components/ui/Badge.tsx`).
Auto-routing is normally invisible infrastructure; here it's legible.

## On the pasted "effects"

Three things were referenced that I want to be upfront about, rather than
quietly pretending to have matched:

- **`glimm`** (the rainbow-shader library in the prompt-bar example) isn't
  something I could verify as an installable package, so there's no shader
  sweep here.
- **`SpecularButton`** and **`ParticleText`** were given only as usage
  examples — prop lists, no implementation. I didn't have their source, so
  I didn't attempt to clone them.

What's actually in this build, rebuilt from scratch in plain CSS/React so
it compiles and runs rather than referencing the unknown:

- **Shimmer loading text** and a **live elapsed timer** (`ShimmerText.tsx`)
  — the same instinct as the referenced "LoadingState" component.
- An **expandable routing trace** (`RoutingTrace.tsx`) — the same instinct
  as the referenced "ThinkingState" component, but wired to this app's
  *real* SSE events (`model_selected`, `retrieval_started`,
  `retrieval_completed`) instead of scripted demo content. What you see
  expand is genuinely what the backend's router and retriever just did.
- A **shine-on-hover button** (`Button.tsx`, `variant="shine"`) — a CSS
  gradient sweep on a pseudo-layer, no canvas/WebGL, used on the chat send
  button.

## What's verified vs. not

This was built in a sandbox with no network access — no `npm install`, no
dev server, no browser. What I could and did verify:

- **A real, strict TypeScript check** (`tsc --strict`) against actual
  React 19 types available locally in the sandbox — not just "it parses."
  Where the sandbox lacked official `@types/react`/`react-router-dom`
  type declarations, I wrote a minimal shim and iteratively tightened it
  (proper `createContext`/`useContext` generics, `useRef` nullability, JSX
  `key` handling, DOM event handler types) until the only remaining
  errors were genuine "module not found" for packages that aren't
  installed — never silenced or ignored, each one individually resolved
  or confirmed as expected.
- All config files (`package.json`, `tsconfig*.json`, `vite.config.ts`,
  `tailwind.config.ts`, `postcss.config.js`) for valid JSON/syntax.

What still needs a real environment: `npm install` (pulls in Vite,
Tailwind, React Router, `@types/*` — none of which exist in this sandbox),
`npm run dev`, and an actual browser to confirm rendering, streaming, and
Tailwind's generated output all behave as expected together. Claude Code
(with network access) is the natural next step for that install → run →
fix loop.

## Project layout

```
src/
  lib/          api client, SSE stream reader, auth + toast contexts
  components/
    ui/         Button, Badge, Modal, Input, ShimmerText
    layout/     Sidebar, AppShell, AuthLayout
    chat/       MessageBubble, RoutingTrace, Composer, ConversationList
  pages/        one per route: chat, agents, knowledge, keys, projects, auth
  types.ts      mirrors the backend's Pydantic schemas
```

Routing is `react-router-dom` (`src/App.tsx`): `/login` and `/register` are
public; everything else nests under `AppShell`, which redirects to
`/login` if there's no valid token and provides the active project via
`useOutletContext` (`src/lib/context.ts`).
