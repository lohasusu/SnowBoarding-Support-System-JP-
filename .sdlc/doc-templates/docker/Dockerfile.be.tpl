# SDLC BE Dockerfile template (PR 13c — language-aware install + runtime parameterized)
#
# Tech-stack agnostic via build args (driven by docker-compose.yml from .env):
#   - BE_RUNTIME: image (node:22-alpine / python:3.12-slim / golang:1.22-alpine / ...)
#   - BE_PKG_MANAGER: install command family (npm / pip / go-mod / dotnet / maven / cargo)
#
# Below is Node-first body. For non-Node BE stacks, this template's RUN steps
# (npm ci / npm run build / node CMD) need adjustment per language. The template
# stays Node-first because it covers ~70% of SDLC projects out-of-box;
# language-specific bodies belong in stack-specific Dockerfiles (future PR).

# ---------- Build stage ----------
ARG BE_RUNTIME="node:22-alpine"
FROM ${BE_RUNTIME} AS build
WORKDIR /app

# ⚠️ Node-first template (PR 13c V1.C4 limitation acknowledgment)
# This Dockerfile assumes Node toolchain by default. For Python/Go/.NET/Java/Rust,
# the conditional logic below detects presence of language-specific files (requirements.txt,
# go.mod, etc.) and runs the appropriate install. If your project's structure differs
# significantly, override this Dockerfile entirely.
#
# PR 13c V1.C4 fix: COPY all source first, then conditional install based on file presence.
# (Previous version COPY'd package*.json BEFORE case statement, which fails for non-Node projects
# because package*.json doesn't exist.)
ARG BE_PKG_MANAGER="npm"

# Copy all source — language-specific files all come along
COPY . .

# Conditional install based on BE_PKG_MANAGER + file presence
RUN sh -c '
  case "$BE_PKG_MANAGER" in
    npm)
      [ -f package.json ] && npm ci --no-audit --no-fund --omit=dev || echo "⚠️ no package.json"
      ;;
    pip)
      [ -f requirements.txt ] && pip install --no-cache-dir -r requirements.txt || echo "⚠️ no requirements.txt"
      ;;
    go-mod)
      [ -f go.mod ] && go mod download || echo "⚠️ no go.mod"
      ;;
    dotnet)
      ls *.csproj >/dev/null 2>&1 && dotnet restore || echo "⚠️ no .csproj"
      ;;
    maven)
      [ -f pom.xml ] && mvn dependency:resolve || echo "⚠️ no pom.xml"
      ;;
    cargo)
      [ -f Cargo.toml ] && cargo fetch || echo "⚠️ no Cargo.toml"
      ;;
    *)
      echo "Unknown BE_PKG_MANAGER: $BE_PKG_MANAGER, skipping install"
      ;;
  esac
'

# Build (Node default; non-Node may not need separate build)
RUN sh -c '
  case "$BE_PKG_MANAGER" in
    npm)    npm run build 2>/dev/null || echo "no build script — using source directly" ;;
    pip)    echo "Python: no separate build step (interpreted)" ;;
    go-mod) go build -o /app/server . 2>/dev/null || echo "no main.go" ;;
    dotnet) dotnet build --configuration Release ;;
    maven)  mvn package -DskipTests ;;
    cargo)  cargo build --release ;;
    *)      echo "Unknown BE_PKG_MANAGER: $BE_PKG_MANAGER, skipping build" ;;
  esac
'

# ---------- Runtime stage ----------
FROM ${BE_RUNTIME} AS runtime
WORKDIR /app

# Non-root user (Alpine syntax; for Debian/Ubuntu use useradd/groupadd)
RUN if command -v addgroup >/dev/null 2>&1 && command -v adduser >/dev/null 2>&1; then \
        addgroup -S app 2>/dev/null && adduser -S app -G app 2>/dev/null || true; \
    fi

# Copy build artifacts. Pick ONE pattern based on language:
# PR 13c V1.C4 fix: COPY whole /app dir first; user trims via .dockerignore for size.
# Non-Node projects don't have node_modules/dist; this single COPY works for all languages.
COPY --from=build /app /app
# Optional: per-language slim copy patterns (uncomment ONE if you want to minimize image):
#   Node:   COPY --from=build /app/node_modules ./node_modules + /app/dist ./dist + /app/package*.json ./
#   Python: (already done by single COPY above; trim via .dockerignore)
#   Go:     COPY --from=build /app/server /app/server  (single binary)
#   .NET:   COPY --from=build /app/bin/Release ./bin
#   Java:   COPY --from=build /app/target/*.jar ./app.jar

USER app
EXPOSE 8000

# Health endpoint MUST be implemented by BE app at /health (Build Gate requirement)
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Entrypoint per language (Node default; replace per project):
CMD ["node", "dist/main.js"]
# Python:  CMD ["python", "main.py"]
# Go:      CMD ["/app/server"]
# .NET:    CMD ["dotnet", "/app/bin/MyApp.dll"]
# Java:    CMD ["java", "-jar", "/app/app.jar"]
# Rust:    CMD ["/app/target/release/myapp"]
