import email.message
import urllib.request

from app.services.runner_service import _NoAuthOnRedirect, _archive_url


def test_archive_url_uses_api_tarball_endpoint():
    url = _archive_url("octo", "repo", "deadbeef")
    assert url == "https://api.github.com/repos/octo/repo/tarball/deadbeef"


def test_redirect_drops_authorization_header():
    handler = _NoAuthOnRedirect()
    request = urllib.request.Request(
        "https://api.github.com/repos/octo/repo/tarball/x",
        headers={
            "Authorization": "Bearer secret-token",
            "Accept": "application/vnd.github+json",
        },
    )

    new_request = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        email.message.Message(),
        "https://codeload.github.com/octo/repo/tar.gz/x?token=signed",
    )

    assert new_request is not None
    assert all(key.lower() != "authorization" for key in new_request.headers)
