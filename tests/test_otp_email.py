from everwealth.auth.models.otp import OneTimePass, _signin_email_message


def test_signin_email_includes_magic_link_and_code():
    otp = OneTimePass(email="test@example.com", code=1234)
    message = _signin_email_message(
        "test@example.com",
        otp,
        "https://app.example.com/login/validate/token_123",
    )

    assert message["To"] == "test@example.com"
    assert message["Subject"] == "Sign in to Everwealth"

    text_body = message.get_body(preferencelist=("plain",)).get_content()
    html_body = message.get_body(preferencelist=("html",)).get_content()

    assert "https://app.example.com/login/validate/token_123" in text_body
    assert "https://app.example.com/login/validate/token_123" in html_body
    assert "1234" in text_body
    assert "1234" in html_body
