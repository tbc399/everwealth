from everwealth.auth.passwords import hash_password, verify_password


def test_password_hash_verifies_original_password():
    password_hash = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", password_hash)


def test_password_hash_rejects_wrong_password():
    password_hash = hash_password("correct horse battery staple")

    assert not verify_password("wrong password", password_hash)
