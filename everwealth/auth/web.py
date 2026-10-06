from datetime import datetime
from typing import Annotated

import stripe
from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import EmailStr

from everwealth.auth.models import otp, sessions, users
from everwealth.auth.passwords import hash_password, verify_password
from everwealth.auth.tokens import create_auth_token
from everwealth.db import get_connection
from everwealth.lucy_config import lucy

from .events import UserCreated

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


def _session_cookie_max_age(session: sessions.Session) -> int:
    return max(0, int((session.expiry - datetime.utcnow()).total_seconds()))


@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    # TODO: check for active session and redirect if found
    return templates.TemplateResponse(request=request, name="auth/login.html")


@router.post("/login", response_class=HTMLResponse)
async def submit_login(
    request: Request,
    identifier: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
):
    user = await users.User.fetch_by_identifier(identifier.strip(), db)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Invalid username/email or password.", "identifier": identifier},
            status_code=401,
        )

    session = await sessions.create(user.id, None, db)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=create_auth_token(user.id, session.id, session.expiry),
        httponly=True,
        samesite="lax",
        max_age=_session_cookie_max_age(session),
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/register.html")


@router.post("/register", response_class=HTMLResponse)
async def submit_register(
    request: Request,
    username: Annotated[str, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    db: Connection = Depends(get_connection),
):
    username = username.strip()
    email = str(email).strip()
    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error": "Password must be at least 8 characters.",
                "username": username,
                "email": email,
            },
            status_code=400,
        )

    if await users.User.fetch_by_username(username, db):
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error": "That username is already taken.",
                "username": username,
                "email": email,
            },
            status_code=409,
        )

    existing_user = await users.User.fetch_by_email(email, db)
    if existing_user and existing_user.password_hash:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error": "That email is already registered.",
                "username": username,
                "email": email,
            },
            status_code=409,
        )

    if existing_user:
        user = await existing_user.set_basic_auth(
            username=username,
            password_hash=hash_password(password),
            conn=db,
        )
    else:
        user = await users.User.create(
            email=email,
            username=username,
            password_hash=hash_password(password),
            conn=db,
        )
        await lucy.publish(UserCreated(user_id=user.id, db=db))

    session = await sessions.create(user.id, None, db)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=create_auth_token(user.id, session.id, session.expiry),
        httponly=True,
        samesite="lax",
        max_age=_session_cookie_max_age(session),
    )
    return response


# the "magic" link sent to the user's email
@router.get("/login/validate/{magic_token}", response_class=HTMLResponse)
async def get_login_validate_page(
    request: Request, magic_token: str, conn: Connection = Depends(get_connection)
):
    # TODO: I think this should return a page directing the user to go back to the original login page
    otpass = await otp.fetch_by_magic_token(magic_token, conn)
    if not otpass:
        logger.info(f"No otp found for magic token {magic_token}")
        return RedirectResponse(url="/sorry", status_code=303)

    return templates.TemplateResponse(
        request=request, name="auth/login-validation.html", context={"otp": otpass}
    )


@router.post("/login/validate/{magic_token}", response_class=HTMLResponse)
async def submit_otp_validation(
    request: Request,
    magic_token: str,
    digit_1: Annotated[int, Form()],
    digit_2: Annotated[int, Form()],
    digit_3: Annotated[int, Form()],
    digit_4: Annotated[int, Form()],
    db: Connection = Depends(get_connection),
):
    # TODO: I think this should return a page directing the user to go back to the original login page
    # TODO: Need to validate otp expiry
    # TODO: Do we validate the device?
    # TODO: validate the # of attempts is under a threshold of 3, for example

    otpass = await otp.fetch_by_magic_token(magic_token, db)
    if not otpass:
        logger.info(f"No otp found for magic token {magic_token}")
        return RedirectResponse(url="/sorry", status_code=303)

    if otpass.is_expired():
        logger.info(f"Otp {otpass.id} has expired")
        # TODO: need a dedicated "has expired" page
        return RedirectResponse(url="/sorry", status_code=303)

    logger.debug(f"Looking for existing user {otpass.email}")
    user = await users.User.fetch_by_email(otpass.email, db)

    if not user:
        user = await users.User.create(otpass.email, db)
        logger.info(f"New user created for {otpass.email}")

        # TODO: This should probably happen in a background task unless asyncio.Queue handles it
        await lucy.publish(UserCreated(user_id=user.id, db=db))

        # TODO: should this be an event handler to let the response come back timely?
        # await stripe.Customer.create_async(name="", email=user.email)

    session = await sessions.create(user.id, otpass.id, db)
    response = templates.TemplateResponse(
        request=request,
        name="auth/login-success.html",
    )
    response.set_cookie(
        key="session",
        value=create_auth_token(user.id, session.id, session.expiry),
        httponly=True,
        samesite="lax",
        max_age=_session_cookie_max_age(session),
    )

    return response


@router.get("/login/{otp_id}", response_class=HTMLResponse)
async def get_login_pending_page(
    request: Request, otp_id: str, conn: Connection = Depends(get_connection)
):
    otpass: otp.OneTimePass = await otp.fetch(otp_id, conn)
    logger.debug(f"otpass found: {otpass.id}")
    if otpass.is_expired():
        # TODO: give back something more specific to this case of the OTP expiring
        return templates.TemplateResponse(request=request, name="404.html", status_code=404)
    return templates.TemplateResponse(
        request=request, name="auth/login-pending.html", context={"otp": otpass}
    )


@router.get("/login/{otp_id}/check")
async def check_login_status(
    request: Request, otp_id: str, conn: Connection = Depends(get_connection)
):
    otpass = await otp.fetch(otp_id, conn)
    if not otpass:
        logger.info(f"Otp {otpass.id} not found")
        return Response(status_code=200, headers={"HX-Redirect": "/sorry"})

    if otpass.is_expired():
        # TODO: need a page to show that otp has expired
        logger.info(f"Otp {otpass.id} has expired")
        return Response(status_code=200, headers={"HX-Redirect": "/sorry"})

    session = await sessions.fetch_by_otp_id(otpass.id, conn)
    logger.info(f"Checking for active session for {otpass.email}")

    if session:
        logger.info(f"Found session {session}")
        response = Response(status_code=200, headers={"HX-Redirect": "/dashboard"})
        response.set_cookie(
            key="session",
            value=create_auth_token(session.user_id, session.id, session.expiry),
            httponly=True,
            samesite="lax",
            max_age=_session_cookie_max_age(session),
        )
        return response

    return Response(status_code=401)


@router.post("/logout", response_class=HTMLResponse)
async def submit_logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session")
    return response


@router.get("/sorry", response_class=HTMLResponse)
def page_not_found(request: Request):
    return templates.TemplateResponse(request=request, name="404.html")
