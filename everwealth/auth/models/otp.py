import random
import smtplib
from asyncio import to_thread
from datetime import datetime, timedelta
from email.message import EmailMessage
from html import escape
from typing import Optional

import shortuuid
from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, EmailStr, Field, PositiveInt


class OneTimePass(BaseModel):
    id: str = Field(default_factory=shortuuid.uuid)
    magic_token: str = Field(default_factory=lambda: shortuuid.random(length=64))
    code: PositiveInt = Field(default_factory=lambda: random.randint(1000, 9999))
    email: EmailStr
    expiry: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invalidated: Optional[bool] = Field(default=False)

    def is_expired(self):
        if self.invalidated:
            return True
        return self.expiry < datetime.utcnow()


async def create(email: str, conn: Connection):
    otp = OneTimePass(email=email)
    async with conn.transaction():
        await conn.execute(
            """
            INSERT INTO otp (id, magic_token, code, email, expiry, created_at, invalidated)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            otp.id,
            otp.magic_token,
            otp.code,
            otp.email,
            otp.expiry,
            otp.created_at,
            otp.invalidated,
        )
    return otp


async def fetch(id: str, conn: Connection):
    row = await conn.fetchrow("SELECT * FROM otp WHERE id = $1", id)
    if row:
        return OneTimePass.model_validate(dict(row))
    return None


async def fetch_by_magic_token(magic_token: str, conn: Connection):
    row = await conn.fetchrow("SELECT * FROM otp WHERE magic_token = $1", magic_token)
    if row:
        return OneTimePass.model_validate(dict(row))
    return None


async def invalidate(id: str, conn: Connection):
    async with conn.transaction():
        await conn.execute("UPDATE otp SET invalidated = true WHERE id = $1", id)


# TODO: move this guy out to a more "service-like" module
async def send_email(email: str, otpass: OneTimePass, magic_url: str):
    from everwealth.config import settings

    logger.info(f"sending otp email to {email} via {settings.smtp_host or 'unconfigured SMTP'}")
    message = _signin_email_message(
        email,
        otpass,
        magic_url,
        app_name=settings.app_name,
        from_email=settings.smtp_from_email,
    )
    sent = await to_thread(
        _send_smtp_message,
        message,
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=settings.smtp_use_tls,
    )
    if sent:
        logger.info(f"sent otp email to {email}")


def _signin_email_message(
    email: str,
    otpass: OneTimePass,
    magic_url: str,
    app_name: str = "Everwealth",
    from_email: str = "no-reply@everwealth.local",
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = f"Sign in to {app_name}"
    message["From"] = from_email
    message["To"] = email

    text_body = f"""Sign in to {app_name}

Click this link to continue signing in:
{magic_url}

Your sign-in code is {otpass.code}.

This link expires in 5 minutes. If you did not request this email, you can ignore it.
"""
    html_body = f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
    <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:24px;">
      <h1 style="margin:0 0 12px;font-size:20px;line-height:1.3;">Sign in to {escape(app_name)}</h1>
      <p style="margin:0 0 20px;font-size:14px;line-height:1.5;color:#475569;">
        Click the button below to continue signing in.
      </p>
      <p style="margin:0 0 20px;">
        <a href="{escape(magic_url)}" style="display:inline-block;background:#0f766e;color:#ffffff;text-decoration:none;border-radius:6px;padding:10px 14px;font-size:14px;font-weight:600;">
          Sign in
        </a>
      </p>
      <p style="margin:0 0 8px;font-size:14px;line-height:1.5;color:#475569;">
        Or copy and paste this link:
      </p>
      <p style="margin:0 0 20px;font-size:13px;line-height:1.5;word-break:break-all;">
        <a href="{escape(magic_url)}" style="color:#0f766e;">{escape(magic_url)}</a>
      </p>
      <p style="margin:0 0 20px;font-size:14px;line-height:1.5;color:#475569;">
        Your sign-in code is <strong>{otpass.code}</strong>.
      </p>
      <p style="margin:0;font-size:12px;line-height:1.5;color:#64748b;">
        This link expires in 5 minutes. If you did not request this email, you can ignore it.
      </p>
    </div>
  </body>
</html>
"""
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    return message


def _send_smtp_message(
    message: EmailMessage,
    host: str | None,
    port: int,
    username: str | None,
    password: str | None,
    use_tls: bool,
):
    if not host:
        logger.error(
            "SMTP_HOST is not configured; cannot send sign-in email to {}. "
            "Set SMTP_HOST, SMTP_PORT, SMTP_FROM_EMAIL, and credentials if required.",
            message["To"],
        )
        return False

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    return True
