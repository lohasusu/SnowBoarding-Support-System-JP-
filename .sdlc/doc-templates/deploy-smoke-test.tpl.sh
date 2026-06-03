#!/usr/bin/env bash
# deploy-smoke-test.tpl.sh — 部署後 smoke test 模板（PR 12）
#
# Setup:
#   1. Copy this file to project root as `scripts/deploy-smoke-test.sh`
#   2. Adjust ENDPOINTS[] 補上專案實際的 critical endpoints
#   3. CI 在 deploy 完成後立刻呼叫此腳本，失敗即觸發 rollback decision
#
# 用法:
#   bash scripts/deploy-smoke-test.sh [BASE_URL]
#   BASE_URL 預設 http://localhost:3000（local），CI 應傳入 staging/prod URL
#
# 退出碼:
#   0 = 全部 endpoint 通過
#   1 = 有 endpoint 失敗（觸發 rollback）
#   2 = 配置錯誤（ENDPOINTS 為空 / curl 缺失）
#
# 設計原則:
#   - 為每個 critical endpoint 跑 curl，timeout 10s
#   - 連續失敗 3 次才判定為 fail（避免 transient 抖動）
#   - 至少要驗證 2 個 endpoint（包含一個非 health 的業務 endpoint）
#   - 違規（ENDPOINTS 長度 < 2）→ exit 2，提示專案需補上業務驗證

set -u

# V1-W4 + V2.W4 fix: trim leading/trailing whitespace + remove trailing slash
RAW_BASE_URL="${1:-http://localhost:3000}"
BASE_URL="${RAW_BASE_URL#"${RAW_BASE_URL%%[![:space:]]*}"}"   # ltrim
BASE_URL="${BASE_URL%"${BASE_URL##*[![:space:]]}"}"           # rtrim
BASE_URL="${BASE_URL%/}"                                      # remove trailing slash

# ---------- 1. 配置 endpoints（dev 必須 customize） ----------
# 每個 entry 為 "PATH|EXPECTED_HTTP_STATUS|DESCRIPTION"
# 至少要 2 個（含 1 個非 /health 的業務驗證）
ENDPOINTS=(
  "/health|200|Liveness probe"
  # CUSTOMIZE: 加入專案的 critical paths，例如:
  # "/api/v1/users/me|401|未登入應回 401（驗證 auth pipeline）"
  # "/api/v1/products|200|產品列表（驗證 DB 連線）"
)

# ---------- 2. 配置驗證 ----------
if [ "${#ENDPOINTS[@]}" -lt 2 ]; then
  echo "ERROR: ENDPOINTS 至少需要 2 個（包含一個非 /health 的業務驗證）" >&2
  echo "請在 scripts/deploy-smoke-test.sh 補上專案 critical paths" >&2
  exit 2
fi

# V1-W5 fix: 強制 ENDPOINTS 至少要有 1 個非 /health 的 business endpoint
# （驗證 DB / auth / cache 等下游連線；純 liveness probe 不能 cover）
NON_HEALTH_COUNT=0
for entry in "${ENDPOINTS[@]}"; do
  path_only="${entry%%|*}"
  case "$path_only" in
    /health|/healthz|/livez|/readyz|/ready|/ping)
      ;;
    *)
      NON_HEALTH_COUNT=$((NON_HEALTH_COUNT + 1))
      ;;
  esac
done
if [ "$NON_HEALTH_COUNT" -lt 1 ]; then
  echo "ERROR: ENDPOINTS 必須包含至少 1 個非 /health 的業務 endpoint" >&2
  echo "（純 health/liveness probe 無法驗證 DB / auth / cache 等下游連線）" >&2
  echo "請在 scripts/deploy-smoke-test.sh 補上業務 critical path（如 /api/v1/users/me）" >&2
  exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl 未安裝" >&2
  exit 2
fi

# ---------- 3. 執行 smoke test ----------
PASS=0
FAIL=0
FAIL_DETAIL=""

for entry in "${ENDPOINTS[@]}"; do
  IFS='|' read -r path expected desc <<< "$entry"
  url="${BASE_URL}${path}"

  # 連續嘗試 3 次（每次間隔 2 秒）
  attempts=0
  succeeded=0
  status="000"
  while [ "$attempts" -lt 3 ]; do
    attempts=$((attempts + 1))
    # 不用 -fsS（會在連線失敗時把 stdout 也清掉）；改用 -o /dev/null + -w 純抓 http_code
    raw=$(curl -o /dev/null -s -L -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || true)
    status="${raw:-000}"
    if [ "$status" = "$expected" ]; then
      succeeded=1
      break
    fi
    [ "$attempts" -lt 3 ] && sleep 2
  done

  if [ "$succeeded" = "1" ]; then
    echo "✅ $path → $status ($desc)"
    PASS=$((PASS + 1))
  else
    echo "❌ $path → $status (expected $expected) ($desc)"
    FAIL=$((FAIL + 1))
    FAIL_DETAIL+="  - $path expected $expected, got $status\n"
  fi
done

# ---------- 4. 摘要 ----------
echo ""
echo "Smoke Test 摘要 (BASE_URL=$BASE_URL):"
echo "  通過: $PASS"
echo "  失敗: $FAIL"
echo "  總計: ${#ENDPOINTS[@]}"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "失敗詳情:"
  printf "%b" "$FAIL_DETAIL"
  echo ""
  echo "建議: 走 rollback-decision-tree.md 判斷是否回滾（PR 14 將提供）"
  exit 1
fi

echo ""
echo "✅ All smoke tests passed."
exit 0
