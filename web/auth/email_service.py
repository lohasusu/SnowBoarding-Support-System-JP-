"""Email 服務：Resend 主要 + SMTP fallback + stderr dev log。"""
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import httpx

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM    = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
BASE_URL       = os.getenv("BASE_URL", "https://snowboarding-support-system-jp-production.up.railway.app")


def _build_verification_html(username: str, verify_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 40px 0;">
  <div style="max-width: 560px; margin: 0 auto; background: white; border-radius: 8px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
    <h2 style="color: #0d6efd; margin-top: 0;">SnowTrip Japan — Email 驗證</h2>
    <p style="color: #333;">Hi <strong>{username}</strong>，</p>
    <p style="color: #333;">感謝您註冊 SnowTrip Japan！請點擊下方按鈕完成 Email 驗證後即可登入：</p>
    <div style="text-align: center; margin: 36px 0;">
      <a href="{verify_url}"
         style="background-color: #0d6efd; color: white; padding: 14px 36px;
                text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold; display: inline-block;">
        ✅ 驗證我的帳號
      </a>
    </div>
    <p style="color: #888; font-size: 13px;">此連結於 24 小時後失效。如非您本人操作，請忽略此信。</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #aaa; font-size: 12px; text-align: center;">SnowTrip Japan — 一站式日本滑雪行程規劃</p>
  </div>
</body>
</html>"""


async def send_verification_email(to_email: str, username: str, token: str) -> bool:
    """
    寄送驗證信。回傳 True 表示成功。
    優先順序：Resend → SMTP → stderr log（開發模式）
    Resend 429（超量）時自動切換 SMTP。
    """
    verify_url = f"{BASE_URL}/api/auth/verify-email?token={token}"
    subject = "請驗證您的 SnowTrip Japan 帳號"
    html_body = _build_verification_html(username, verify_url)

    # 1. Resend
    if RESEND_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": RESEND_FROM,
                        "to": [to_email],
                        "subject": subject,
                        "html": html_body,
                    },
                )
                if resp.status_code in (200, 201):
                    return True
                # 429 rate-limit → fall through to SMTP
        except Exception:
            pass

    # 2. SMTP fallback
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = smtp_user
            msg["To"]      = to_email
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [to_email], msg.as_string())
            return True
        except Exception as e:
            print(f"[SMTP ERROR] {e}", file=sys.stderr)

    # 3. Dev fallback：印到 stderr，讓開發者可以手動點連結測試
    print(
        f"\n[DEV EMAIL] ========================================\n"
        f"To: {to_email}\nSubject: {subject}\n"
        f"Verify URL: {verify_url}\n"
        f"==========================================\n",
        file=sys.stderr,
    )
    return False
