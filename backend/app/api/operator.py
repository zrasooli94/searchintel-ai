import hmac

from fastapi import Header, HTTPException

from app.core.config import settings


def require_operator(
    x_searchintel_operator: str = Header(
        default="",
    ),
) -> None:
    if settings.api_token is None:
        return

    expected = settings.api_token.get_secret_value()
    if not hmac.compare_digest(
        x_searchintel_operator,
        expected,
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Authorized operator access is required "
                "for paid AI execution."
            ),
        )
