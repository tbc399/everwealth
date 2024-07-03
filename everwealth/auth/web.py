from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import EmailStr

from everwealth.auth.models import otp, sessions, users
from everwealth.db import get_connection
from everwealth.lucy_config import lucy

from .events import UserCreated

router = APIRouter()

templates = Jinja2Templates(directory="everwealth/templates")


@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    # TODO: check for active session and redirect if found
    return templates.TemplateResponse(request=request, name="auth/login.html")


@router.post("/login", response_class=HTMLResponse)
async def submit_login(
    request: Request,
    email: Annotated[EmailStr, Form()],
    tasks: BackgroundTasks,
    db: Connection = Depends(get_connection),
):
    # TODO: have to pull a session from the cookies or else do a new auth flow

    # user = await users.fetch(email, conn)
    # if user:
    #    logger.info(f"User with email {email} already exists")
    #    session = await sessions.fetch_latest_active(user.id, conn)
    #    if session:
    #        logger.info(f"User {user.id} has an active session. Redirecting back to dashboard")
    #        return RedirectResponse(url="dashboard", status_code=303)
    #    else:
    #        logger.info(f"user {user.id} does not currently have an active session")
    # else:
    #    logger.info(f"no user exists for email {email}")

    # TODO: need to invalidate any currently active otps when creating a new one
    otpass = await otp.create(email, db)
    tasks.add_task(otp.send_email, email, otpass)

    return RedirectResponse(
        url=f"/login/{otpass.id}", status_code=303
    )  # TODO: redirect to other page


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
    user = await users.fetch_by_email(otpass.email, db)

    if not user:
        user = await users.create(otpass.email, db)
        logger.info(f"New user created for {otpass.email}")

        # TODO: This should probably happen in a background task
        await lucy.publish(UserCreated(user_id=user.id, db=db))

    _ = await sessions.create(user.id, otpass.id, db)

    return templates.TemplateResponse(
        request=request,
        name="auth/login-success.html",
    )


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
        response.set_cookie(key="session", value=session.id)
        return response

    return Response(status_code=401)


@router.post("/logout", response_class=HTMLResponse)
async def submit_logout(request: Request, conn: Connection = Depends(get_connection)):
    # Need to invalidate session and notify the browser to invalidate its session cookie
    sessions.invalidate("", conn)
    return


@router.get("/sorry", response_class=HTMLResponse)
def page_not_found(request: Request):
    return templates.TemplateResponse(request=request, name="404.html")
