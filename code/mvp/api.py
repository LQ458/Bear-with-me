"""HTTP transport for the MVP services.

This layer performs authentication extraction and serialization only; business
rules live in the domain modules.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import Depends, FastAPI, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import Settings
from .container import Services, create_services
from .demo import bootstrap as bootstrap_recording
from .errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    CryptoError,
    MvpError,
    NotFoundError,
    ProviderUnavailable,
    RateLimitError,
    ValidationError,
)
from .models import AuthorityCaseStatus, ItemStatus
from .rate_limit import RateLimiter


class RegisterBody(BaseModel):
    email: str
    name: str = Field(min_length=1, max_length=120)


class MagicLinkBody(BaseModel):
    email: str


class ConsumeBody(BaseModel):
    token: str = Field(min_length=20)


class ItemBody(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class StatusBody(BaseModel):
    status: ItemStatus


class FoundBody(BaseModel):
    place: str
    note: str = Field(default="", max_length=1000)
    authority_organization: str = Field(default="", max_length=160)


class MessageBody(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class DeviceBody(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    platform: str


class AuthorityInviteBody(BaseModel):
    organization: str = Field(min_length=1, max_length=160)
    email: str


class AuthorityAcceptBody(BaseModel):
    token: str = Field(min_length=20)
    name: str = Field(min_length=1, max_length=120)


class AuthorityUpdateBody(BaseModel):
    status: AuthorityCaseStatus
    case_number: str | None = Field(default=None, max_length=120)


class CallTokenResponse(BaseModel):
    server_url: str
    room: str
    token: str


def create_app(services: Services | None = None) -> FastAPI:
    if services is None:
        services = create_services(Settings.from_env())
    app = FastAPI(title="Whoops Tag", version="0.1.0")
    app.state.services = services
    app.state.rate_limiter = RateLimiter()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[services.settings.web_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Finder-Session", "X-Platform-Admin"],
    )

    @app.exception_handler(MvpError)
    async def mvp_error_handler(request: Request, exc: MvpError):
        mapping = {
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            NotFoundError: status.HTTP_404_NOT_FOUND,
            ConflictError: status.HTTP_409_CONFLICT,
            ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
            ProviderUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
            CryptoError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        code = next((value for error, value in mapping.items() if isinstance(exc, error)), 400)
        headers = {"Retry-After": str(exc.retry_after)} if isinstance(exc, RateLimitError) else None
        return JSONResponse(status_code=code if not isinstance(exc, RateLimitError) else status.HTTP_429_TOO_MANY_REQUESTS, content={"error": str(exc)}, headers=headers)

    def svc() -> Services:
        return app.state.services

    def auth_header(authorization: Annotated[str | None, Header()] = None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthenticationError("bearer authentication required")
        return authorization[7:].strip()

    def finder_header(x_finder_session: Annotated[str | None, Header()] = None) -> str:
        if not x_finder_session:
            raise AuthenticationError("finder session required")
        return x_finder_session

    def client_ip(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    def throttle(request: Request, bucket: str, limit: int) -> None:
        app.state.rate_limiter.check(f"{bucket}:{client_ip(request)}", limit, 60)

    def throttle_session(request: Request, session_token: str) -> None:
        from .util import hash_token

        app.state.rate_limiter.check(
            f"finder-report:{client_ip(request)}:{hash_token(session_token)[:16]}",
            5,
            60,
        )

    def throttle_human_code(request: Request, human_code: str) -> None:
        from .util import hash_token

        app.state.rate_limiter.check(f"finder-code-ip:{client_ip(request)}", 10, 60)
        app.state.rate_limiter.check(
            f"finder-code-value:{hash_token(human_code.upper())[:16]}", 10, 60
        )


    @app.api_route("/api/recording/bootstrap", methods=["GET", "POST"])
    def recording_bootstrap(services: Services = Depends(svc)):
        return bootstrap_recording(services)

    @app.get("/api/f/{secret}")
    def open_finder_secret(request: Request, secret: str, services: Services = Depends(svc)):
        throttle(request, "finder-secret", 60)
        finder = services.finder.open_secret(secret)
        return {"session_token": finder.session_token, "label": finder.label}

    @app.get("/api/f/code/{human_code}")
    def open_finder_code(request: Request, human_code: str, services: Services = Depends(svc)):
        throttle_human_code(request, human_code)
        finder = services.finder.open_human_code(human_code)
        return {"session_token": finder.session_token, "label": finder.label}

    @app.post("/api/f/sessions/{session_token}/found")
    def report_found(request: Request, session_token: str, body: FoundBody, services: Services = Depends(svc)):
        throttle_session(request, session_token)
        report = services.finder.report_found(
            session_token,
            body.place,
            body.note,
            body.authority_organization,
        )
        return {
            "found_ref": report.found_ref,
            "conversation_ref": report.conversation_ref,
            "place": report.place,
            "authority_case_ref": report.authority_case_ref,
            "created_at": report.created_at,
        }

    @app.post("/api/auth/register")
    def register(body: RegisterBody, services: Services = Depends(svc)):
        user, session = services.identity.register(body.email, body.name)
        return {"user": asdict(user), "session_token": session}

    @app.post("/api/auth/magic-link/request")
    def request_magic(body: MagicLinkBody, services: Services = Depends(svc)):
        return {"token": services.identity.request_magic_link(body.email)}

    @app.post("/api/auth/magic-link/consume")
    def consume_magic(body: ConsumeBody, services: Services = Depends(svc)):
        user, session = services.identity.consume_magic_link(body.token)
        return {"user": asdict(user), "session_token": session}

    @app.get("/api/items")
    def list_items(token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return {"items": [asdict(item) for item in services.items.list_items(user.user_ref)]}

    @app.post("/api/items")
    def create_item(body: ItemBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return asdict(services.items.create_item(user.user_ref, body.label, body.description))

    @app.patch("/api/items/{item_ref}")
    def rename_item(item_ref: str, body: ItemBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return asdict(services.items.rename_item(user.user_ref, item_ref, body.label, body.description))

    @app.post("/api/items/{item_ref}/status")
    def set_item_status(item_ref: str, body: StatusBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return asdict(services.items.set_status(user.user_ref, item_ref, body.status))

    @app.post("/api/items/{item_ref}/tags")
    def provision_tag(item_ref: str, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return asdict(services.items.provision_tag(user.user_ref, item_ref))

    @app.post("/api/tags/{tag_ref}/revoke")
    def revoke_tag(tag_ref: str, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        services.items.revoke_tag(user.user_ref, tag_ref)
        return {"status": "revoked"}

    @app.post("/api/tags/{tag_ref}/replace")
    def replace_tag(tag_ref: str, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return asdict(services.items.replace_tag(user.user_ref, tag_ref))


    @app.get("/api/owner/inbox")
    def owner_inbox(token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return {"events": services.finder.owner_inbox(user.user_ref)}

    @app.get("/api/owner/conversations/{conversation_ref}/messages")
    def owner_messages(conversation_ref: str, after: str = "", token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return {"messages": [asdict(message) for message in services.chat.list_for_owner(user.user_ref, conversation_ref, after)]}

    @app.post("/api/owner/conversations/{conversation_ref}/messages")
    def owner_send(conversation_ref: str, body: MessageBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return asdict(services.chat.send_owner(user.user_ref, conversation_ref, body.body))

    @app.get("/api/finder/conversations/{conversation_ref}/messages")
    def finder_messages(conversation_ref: str, after: str = "", session: str = Depends(finder_header), services: Services = Depends(svc)):
        return {"messages": [asdict(message) for message in services.chat.list_for_finder(session, conversation_ref, after)]}

    @app.post("/api/finder/conversations/{conversation_ref}/messages")
    def finder_send(conversation_ref: str, body: MessageBody, session: str = Depends(finder_header), services: Services = Depends(svc)):
        return asdict(services.chat.send_finder(session, conversation_ref, body.body))

    @app.post("/api/owner/devices")
    def register_device(body: DeviceBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        device_ref = services.notifications.register_device(user.user_ref, body.token, body.platform)
        return {"device_ref": device_ref}

    @app.post("/api/admin/authority-invites")
    def invite_authority(body: AuthorityInviteBody, x_platform_admin: Annotated[str | None, Header()] = None, services: Services = Depends(svc)):
        return {"invite_token": services.authorities.invite(x_platform_admin or "", body.organization, body.email)}

    @app.post("/api/authority/accept")
    def accept_authority(body: AuthorityAcceptBody, services: Services = Depends(svc)):
        user, session = services.authorities.accept_invite(body.token, body.name)
        return {"user": asdict(user), "session_token": session}

    @app.get("/api/authority/cases")
    def authority_cases(token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_authority(token)
        return {"cases": [asdict(case) for case in services.authorities.list_cases(user.user_ref)]}

    @app.post("/api/authority/cases/{case_ref}")
    def authority_update(case_ref: str, body: AuthorityUpdateBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_authority(token)
        return asdict(services.authorities.update_case(user.user_ref, case_ref, body.status, body.case_number))

    @app.get("/api/authority/conversations/{conversation_ref}/messages")
    def authority_messages(conversation_ref: str, after: str = "", token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_authority(token)
        lookup = services.authorities.organization_lookup_for_user(user.user_ref)
        return {"messages": [asdict(message) for message in services.chat.list_for_authority(lookup, conversation_ref, after)]}

    @app.post("/api/authority/conversations/{conversation_ref}/messages")
    def authority_send(conversation_ref: str, body: MessageBody, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_authority(token)
        lookup = services.authorities.organization_lookup_for_user(user.user_ref)
        return asdict(services.chat.send_authority(user.user_ref, lookup, conversation_ref, body.body))

    @app.post("/api/owner/conversations/{conversation_ref}/call-token", response_model=CallTokenResponse)
    def owner_call(conversation_ref: str, token: str = Depends(auth_header), services: Services = Depends(svc)):
        user = services.identity.require_owner(token)
        return services.calling.owner_token(user.user_ref, conversation_ref)

    @app.post("/api/finder/conversations/{conversation_ref}/call-token", response_model=CallTokenResponse)
    def finder_call(conversation_ref: str, session: str = Depends(finder_header), services: Services = Depends(svc)):
        return services.calling.finder_token(session, conversation_ref)

    return app
