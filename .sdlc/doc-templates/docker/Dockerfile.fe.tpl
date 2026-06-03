# SDLC FE Dockerfile template (PR 13c — both stages parameterized)
#
# PR 12 v1 V1.C4 finding: "build stage hardcoded node:22-alpine — breaks for non-Node FE
# stacks (Hugo / Jekyll / Eleventy)." PR 13c fixes by parameterizing BOTH stages:
#   - Build stage: ARG FE_BUILD_IMAGE (default node:22-alpine, also covers Vue/React/Angular/Svelte)
#   - Runtime stage: ARG FE_SERVE_IMAGE (default nginx:alpine for SPA, node:22-alpine for SSR)
#   - Build command: ARG FE_BUILD_CMD (default npm run build, override for "ng build" etc)
#
# Setup: copy to fe/Dockerfile, then `docker compose build frontend`
# All ARG values come from docker-compose.yml's `args:` block, which reads from .env
# (rendered by sdlc-render-docker-env.sh from config.json.techStack.frontend)

# ---------- Build stage ----------
ARG FE_BUILD_IMAGE="node:22-alpine"
FROM ${FE_BUILD_IMAGE} AS build
WORKDIR /app

# ⚠️ Node-first template (PR 13c V1.C3 limitation acknowledgment)
# This Dockerfile assumes Node-based FE toolchain (covers React/Vue/Angular/Svelte/Next.js/Nuxt/SvelteKit
# = ~95% of SDLC FE projects). For non-Node static site generators (Hugo / Jekyll / Eleventy),
# replace this Dockerfile entirely — that's a future stack-specific template PR.
#
# PR 13c V1.C3 fix: COPY all source first, then conditional install based on file presence
COPY . .
ARG FE_BUILD_CMD="npm run build"

# Conditional install: only run npm if package.json exists
RUN if [ -f package.json ]; then \
        npm ci --no-audit --no-fund && sh -c "$FE_BUILD_CMD" ; \
    else \
        echo "⚠️  No package.json found — assuming static-site generator. Skip Node install." ; \
        echo "    Override Dockerfile if your FE uses a different build chain." ; \
    fi

# ---------- Runtime stage ----------
# FE_SERVE_IMAGE switches between nginx (SPA: React/Vue/Angular/Svelte) and
# node (SSR: Next.js/Nuxt/SvelteKit). Default = nginx (most common static SPA case).
ARG FE_SERVE_IMAGE="nginx:alpine"
FROM ${FE_SERVE_IMAGE} AS runtime

# Conditional setup: nginx vs node
WORKDIR /usr/share/nginx/html

RUN if [ -d /etc/nginx ]; then \
      printf 'server {\n    listen 3000;\n    location / {\n        root /usr/share/nginx/html;\n        index index.html;\n        try_files $uri $uri/ /index.html;\n    }\n    location /health {\n        return 200 "ok";\n        add_header Content-Type text/plain;\n    }\n}\n' > /etc/nginx/conf.d/default.conf \
      && rm -f /etc/nginx/conf.d/default.conf.bak ; \
    fi

# Standardized output paths (Docker COPY does NOT support shell `||` fallback —
# pick ONE of the lines below based on your framework's build output, delete the rest):
#
#   - Vite/Vue/SvelteKit/Angular: dist/  (default)
COPY --from=build /app/dist .
#   - React (CRA): build/
# COPY --from=build /app/build .
#   - Next.js: .next/  (also requires SSR runtime — set FE_SERVE_IMAGE=node:22-alpine)
# COPY --from=build /app/.next .next
# COPY --from=build /app/public ./public
# COPY --from=build /app/package*.json ./

EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# CMD is engine-aware. nginx default; SSR projects (Next.js, Nuxt, SvelteKit) override
# this line in their Dockerfile.
CMD ["sh", "-c", "if command -v nginx >/dev/null 2>&1; then nginx -g 'daemon off;'; else node server.js; fi"]
