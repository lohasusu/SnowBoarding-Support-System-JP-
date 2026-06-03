# .github/CODEOWNERS — required reviewers for SDLC-critical files
#
# Why (V3 / Rule 19.5): without required reviewers on .github/workflows/
# and scripts/, a malicious PR can rewrite sdlc-merge-gate.yml to `exit 0`
# and bypass all CI gates. CODEOWNERS forces a human review for these
# files. This template is installed by /sdlc:init Step 4.17.
#
# Setup (one-time, in GitHub UI):
#   Settings → Branch protection rule for `main`
#     → ✅ Require review from Code Owners
#
# Replace @your-team and @your-org/sdlc-maintainers with actual teams.

# All SDLC CI workflows — must be reviewed by maintainers
.github/workflows/sdlc-*.yml             @your-org/sdlc-maintainers
.github/CODEOWNERS                       @your-org/sdlc-maintainers

# SDLC scripts — change-control gate
scripts/sdlc-*.sh                        @your-org/sdlc-maintainers

# Layer 2 conventions — RFC required (Rule 16)
.sdlc/conventions/**                     @your-org/sdlc-maintainers

# Design system canonical — RFC required (Rule 17)
.sdlc/conventions/design-system.pen      @your-org/sdlc-maintainers
.sdlc/conventions/design-system.meta.json @your-org/sdlc-maintainers

# ID allocator — multi-dev safe partitioning, must not be hand-edited
.sdlc/id-allocator.json                  @your-org/sdlc-maintainers

# CUSTOMIZE: add team-specific patterns below
# frontend/**                            @your-org/frontend
# backend/**                             @your-org/backend
