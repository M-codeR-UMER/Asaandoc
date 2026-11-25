from datetime import datetime, timedelta, timezone
import hashlib

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.dependencies import get_session
from app.config import db_settings
from app.database.models import RefreshToken
from app.main import app


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        url=db_settings.POSTGRES_URL,
        connect_args={"ssl": False},
    )
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cors_preflight(client: AsyncClient):
    response = await client.options(
        "/doctor/token",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_doctor_signup_login_dashboard_and_cross_role_rejection(
    client: AsyncClient,
):
    signup_payload = {
        "name": "Dr. Ayesha Khan",
        "email": "Phase0.Doctor@Example.com",
        "phone_number": "+923001112233",
        "password": "StrongPassword123!",
        "terms_accepted": True,
    }
    res = await client.post("/doctor/signup", json=signup_payload)
    assert res.status_code == 201, res.text
    doctor_data = res.json()
    assert doctor_data["email"] == "phase0.doctor@example.com"
    assert "password_hash" not in doctor_data

    # Invalid non-Pakistani phone on doctor signup -> 422
    bad_doc_res = await client.post(
        "/doctor/signup",
        json={
            "name": "Dr. Test",
            "email": "badphone.doctor@example.com",
            "phone_number": "+14155552671",
            "password": "StrongPassword123!",
            "terms_accepted": True,
        },
    )
    assert bad_doc_res.status_code == 422

    # Duplicate email (case-insensitive) -> 409 Conflict
    dup_res = await client.post(
        "/doctor/signup",
        json={**signup_payload, "email": "phase0.doctor@example.com"},
    )
    assert dup_res.status_code == 409

    # Login with uppercase email -> 200 OK
    login_res = await client.post(
        "/doctor/token",
        data={
            "username": "PHASE0.DOCTOR@EXAMPLE.COM",
            "password": "StrongPassword123!",
        },
    )
    assert login_res.status_code == 200, login_res.text
    tokens = login_res.json()
    assert tokens["role"] == "doctor"
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 3600
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    dash_res = await client.get("/doctor/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["email"] == "phase0.doctor@example.com"
    assert "password_hash" not in dash_data

    # Cross-role token must be rejected with 401
    cross_res = await client.get("/patient/dashboard", headers=headers)
    assert cross_res.status_code == 401


@pytest.mark.asyncio
async def test_patient_pakistani_phone_auth_and_cross_role_rejection(
    client: AsyncClient,
):
    # Invalid / non-Pakistani numbers -> 422
    for bad_phone in ["0511234567", "+14155552671", "not-a-phone", "12345"]:
        bad_res = await client.post(
            "/patient/signup",
            json={
                "name": "Ali Raza",
                "phone_number": bad_phone,
                "password": "StrongPassword123!",
                "terms_accepted": True,
            },
        )
        assert bad_res.status_code == 422, f"Expected 422 for {bad_phone}"

    # Valid Pakistani mobile in local format -> normalized E.164
    res = await client.post(
        "/patient/signup",
        json={
            "name": "Ali Raza",
            "phone_number": "03001234567",
            "password": "StrongPassword123!",
            "terms_accepted": True,
        },
    )
    assert res.status_code == 201, res.text
    patient_data = res.json()
    assert patient_data["phone_number"] == "+923001234567"
    assert patient_data["city"] == "Lahore"
    assert "password_hash" not in patient_data

    # Duplicate normalized number -> 409 Conflict
    dup_res = await client.post(
        "/patient/signup",
        json={
            "name": "Ali Raza",
            "phone_number": "+923001234567",
            "password": "StrongPassword123!",
            "terms_accepted": True,
        },
    )
    assert dup_res.status_code == 409

    # Invalid phone on login -> 422
    bad_login = await client.post(
        "/patient/token",
        data={"username": "+14155552671", "password": "StrongPassword123!"},
    )
    assert bad_login.status_code == 422

    # Valid login using +92 format -> 200 OK
    login_res = await client.post(
        "/patient/token",
        data={"username": "+923001234567", "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200, login_res.text
    tokens = login_res.json()
    assert tokens["role"] == "patient"

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    dash_res = await client.get("/patient/dashboard", headers=headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["phone_number"] == "+923001234567"
    assert "password_hash" not in dash_res.json()

    # Cross-role token must be rejected with 401
    cross_res = await client.get("/doctor/dashboard", headers=headers)
    assert cross_res.status_code == 401


@pytest.mark.asyncio
async def test_doctor_refresh_token_24h_cap_and_logout_revocation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    await client.post(
        "/doctor/signup",
        json={
            "name": "Dr. Bilal",
            "email": "bilal.phase0@example.com",
            "phone_number": "+923211234567",
            "password": "StrongPassword123!",
            "terms_accepted": True,
        },
    )
    login_res = await client.post(
        "/doctor/token",
        data={
            "username": "bilal.phase0@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert login_res.status_code == 200
    tokens_1 = login_res.json()

    # Confirm DB max_expires_at is capped at 24 hours from creation
    hash_1 = hashlib.sha256(tokens_1["refresh_token"].encode("utf-8")).hexdigest()
    rec_1 = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_1)
        )
    ).scalar_one()
    lifetime = rec_1.max_expires_at - rec_1.created_at
    assert timedelta(hours=23, minutes=59) <= lifetime <= timedelta(hours=24, seconds=5)

    # Rotate once
    ref_res = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens_1["refresh_token"]},
    )
    assert ref_res.status_code == 200, ref_res.text
    tokens_2 = ref_res.json()
    assert tokens_2["refresh_token"] != tokens_1["refresh_token"]

    # Old refresh token cannot be reused
    reuse_res = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens_1["refresh_token"]},
    )
    assert reuse_res.status_code == 401

    # Simulate max_expires_at only 10 minutes left: rotated token must NOT extend past max_expires_at
    hash_2 = hashlib.sha256(tokens_2["refresh_token"].encode("utf-8")).hexdigest()
    rec_2 = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_2)
        )
    ).scalar_one()
    capped_max = datetime.now(timezone.utc) + timedelta(minutes=10)
    rec_2.max_expires_at = capped_max
    rec_2.expires_at = capped_max
    await db_session.commit()

    ref_res_3 = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens_2["refresh_token"]},
    )
    assert ref_res_3.status_code == 200
    tokens_3 = ref_res_3.json()
    assert tokens_3["expires_in"] <= 600

    hash_3 = hashlib.sha256(tokens_3["refresh_token"].encode("utf-8")).hexdigest()
    rec_3 = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_3)
        )
    ).scalar_one()
    assert rec_3.expires_at <= capped_max
    assert rec_3.max_expires_at <= capped_max

    # Logout revokes both access jti in Redis and refresh token in DB
    logout_res = await client.post(
        "/doctor/logout",
        headers={"Authorization": f"Bearer {tokens_3['access_token']}"},
        json={"refresh_token": tokens_3["refresh_token"]},
    )
    assert logout_res.status_code == 200

    dash_after_logout = await client.get(
        "/doctor/dashboard",
        headers={"Authorization": f"Bearer {tokens_3['access_token']}"},
    )
    assert dash_after_logout.status_code == 401

    refresh_after_logout = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens_3["refresh_token"]},
    )
    assert refresh_after_logout.status_code == 401
