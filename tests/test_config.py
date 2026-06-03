from cb_monitor.config import Settings


def test_settings_treat_blank_cookie_as_unset() -> None:
    settings = Settings.model_validate({"cookie": "", "cookie_file": "cookies.txt"})

    assert settings.cookie is None
    assert settings.cookie_file is not None


def test_settings_treat_blank_proxy_as_unset() -> None:
    settings = Settings.model_validate(
        {"cookie_file": "cookies.txt", "proxy_url": "  "}
    )

    assert settings.proxy_url is None
