import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from .. import crud, models, schemas
from ..security import get_password_hash, create_access_token
from datetime import timedelta
from ..config import settings

# Assuming conftest.py sets up client and db_session fixtures

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Auth Service is running!"}

def test_register_user(client: TestClient, db_session: Session):
    # Test successful registration
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "is_active" in data
    assert data["is_active"] is True
    assert "roles" in data
    assert data["roles"] == []

    # Verify user is in DB
    user = crud.get_user_by_email(db_session, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"

    # Test duplicate registration
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_for_access_token(client: TestClient, db_session: Session):
    # First, register a user
    crud.create_user(db_session, schemas.UserCreate(email="login@example.com", password="password123"))

    # Test successful login
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test incorrect password
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

    # Test unregistered user
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_read_users_me(client: TestClient, db_session: Session):
    user_email = "me@example.com"
    crud.create_user(db_session, schemas.UserCreate(email=user_email, password="password123"))

    # Get token
    login_response = client.post(
        "/auth/login",
        data={"username": user_email, "password": "password123"}
    )
    token = login_response.json()["access_token"]

    # Test access with valid token
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_email
    assert "id" in data

    # Test access without token
    response = client.get("/auth/me")
    assert response.status_code == 401

    # Test access with invalid token (e.g., expired or malformed)
    # For simplicity, we'll just use a clearly invalid token string
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_create_role(client: TestClient, db_session: Session):
    # Create an admin user
    admin_user = crud.create_user(db_session, schemas.UserCreate(email="admin@example.com", password="adminpassword"))
    admin_role = crud.create_role(db_session, schemas.RoleCreate(name="admin"))
    crud.assign_roles_to_user(db_session, admin_user, ["admin"])

    admin_login_response = client.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": "adminpassword"}
    )
    admin_token = admin_login_response.json()["access_token"]

    # Test creating a role as admin
    response = client.post(
        "/auth/roles/",
        json={"name": "editor"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "editor"
    assert "id" in data

    # Test creating a duplicate role
    response = client.post(
        "/auth/roles/",
        json={"name": "editor"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Role with this name already exists"

    # Test creating a role without admin permissions
    normal_user = crud.create_user(db_session, schemas.UserCreate(email="normal@example.com", password="password123"))
    normal_login_response = client.post(
        "/auth/login",
        data={"username": "normal@example.com", "password": "password123"}
    )
    normal_token = normal_login_response.json()["access_token"]

    response = client.post(
        "/auth/roles/",
        json={"name": "viewer"},
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

def test_read_roles(client: TestClient, db_session: Session):
    # Create an admin user
    admin_user = crud.create_user(db_session, schemas.UserCreate(email="admin_read@example.com", password="adminpassword"))
    admin_role = crud.create_role(db_session, schemas.RoleCreate(name="admin"))
    crud.assign_roles_to_user(db_session, admin_user, ["admin"])

    admin_login_response = client.post(
        "/auth/login",
        data={"username": "admin_read@example.com", "password": "adminpassword"}
    )
    admin_token = admin_login_response.json()["access_token"]

    # Create some roles
    crud.create_role(db_session, schemas.RoleCreate(name="role1"))
    crud.create_role(db_session, schemas.RoleCreate(name="role2"))

    # Test reading roles as admin
    response = client.get(
        "/auth/roles/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) >= 3 # admin, role1, role2
    role_names = {r["name"] for r in roles}
    assert "admin" in role_names
    assert "role1" in role_names
    assert "role2" in role_names

    # Test reading roles without admin permissions
    normal_user = crud.create_user(db_session, schemas.UserCreate(email="normal_read@example.com", password="password123"))
    normal_login_response = client.post(
        "/auth/login",
        data={"username": "normal_read@example.com", "password": "password123"}
    )
    normal_token = normal_login_response.json()["access_token"]

    response = client.get(
        "/auth/roles/",
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

def test_assign_roles_to_user(client: TestClient, db_session: Session):
    # Create an admin user
    admin_user = crud.create_user(db_session, schemas.UserCreate(email="admin_assign@example.com", password="adminpassword"))
    admin_role = crud.create_role(db_session, schemas.RoleCreate(name="admin"))
    crud.assign_roles_to_user(db_session, admin_user, ["admin"])

    admin_login_response = client.post(
        "/auth/login",
        data={"username": "admin_assign@example.com", "password": "adminpassword"}
    )
    admin_token = admin_login_response.json()["access_token"]

    # Create a target user and some roles
    target_user = crud.create_user(db_session, schemas.UserCreate(email="target@example.com", password="password123"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleA"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleB"))

    # Test assigning roles as admin
    response = client.post(
        f"/auth/users/{target_user.id}/roles/",
        json={"role_names": ["roleA", "roleB"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "target@example.com"
    assigned_role_names = {r["name"] for r in data["roles"]}
    assert "roleA" in assigned_role_names
    assert "roleB" in assigned_role_names

    # Verify in DB
    updated_user = crud.get_user_by_id(db_session, target_user.id)
    assert len(updated_user.roles) == 2
    assert {r.name for r in updated_user.roles} == {"roleA", "roleB"}

    # Test assigning a non-existent role
    response = client.post(
        f"/auth/users/{target_user.id}/roles/",
        json={"role_names": ["nonexistent_role"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Role 'nonexistent_role' not found"

    # Test assigning roles to a non-existent user
    response = client.post(
        "/auth/users/9999/roles/",
        json={"role_names": ["roleA"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    # Test assigning roles without admin permissions
    normal_user = crud.create_user(db_session, schemas.UserCreate(email="normal_assign@example.com", password="password123"))
    normal_login_response = client.post(
        "/auth/login",
        data={"username": "normal_assign@example.com", "password": "password123"}
    )
    normal_token = normal_login_response.json()["access_token"]

    response = client.post(
        f"/auth/users/{target_user.id}/roles/",
        json={"role_names": ["roleA"]},
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

def test_get_user_roles(client: TestClient, db_session: Session):
    # Create an admin user
    admin_user = crud.create_user(db_session, schemas.UserCreate(email="admin_get_user_roles@example.com", password="adminpassword"))
    admin_role = crud.create_role(db_session, schemas.RoleCreate(name="admin"))
    crud.assign_roles_to_user(db_session, admin_user, ["admin"])

    admin_login_response = client.post(
        "/auth/login",
        data={"username": "admin_get_user_roles@example.com", "password": "adminpassword"}
    )
    admin_token = admin_login_response.json()["access_token"]

    # Create a target user and assign roles
    target_user = crud.create_user(db_session, schemas.UserCreate(email="target_get_roles@example.com", password="password123"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleX"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleY"))
    crud.assign_roles_to_user(db_session, target_user, ["roleX", "roleY"])

    # Test getting user roles as admin
    response = client.get(
        f"/auth/users/{target_user.id}/roles/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    roles = response.json()
    assert len(roles) == 2
    role_names = {r["name"] for r in roles}
    assert "roleX" in role_names
    assert "roleY" in role_names

    # Test getting roles for a non-existent user
    response = client.get(
        "/auth/users/9999/roles/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    # Test getting user roles without admin permissions
    normal_user = crud.create_user(db_session, schemas.UserCreate(email="normal_get_roles@example.com", password="password123"))
    normal_login_response = client.post(
        "/auth/login",
        data={"username": "normal_get_roles@example.com", "password": "password123"}
    )
    normal_token = normal_login_response.json()["access_token"]

    response = client.get(
        f"/auth/users/{target_user.id}/roles/",
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

def test_remove_roles_from_user(client: TestClient, db_session: Session):
    # Create an admin user
    admin_user = crud.create_user(db_session, schemas.UserCreate(email="admin_remove@example.com", password="adminpassword"))
    admin_role = crud.create_role(db_session, schemas.RoleCreate(name="admin"))
    crud.assign_roles_to_user(db_session, admin_user, ["admin"])

    admin_login_response = client.post(
        "/auth/login",
        data={"username": "admin_remove@example.com", "password": "adminpassword"}
    )
    admin_token = admin_login_response.json()["access_token"]

    # Create a target user and assign roles
    target_user = crud.create_user(db_session, schemas.UserCreate(email="target_remove_roles@example.com", password="password123"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleP"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleQ"))
    crud.create_role(db_session, schemas.RoleCreate(name="roleR"))
    crud.assign_roles_to_user(db_session, target_user, ["roleP", "roleQ", "roleR"])

    # Test removing roles as admin
    response = client.delete(
        f"/auth/users/{target_user.id}/roles/",
        json={"role_names": ["roleP", "roleQ"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "target_remove_roles@example.com"
    remaining_role_names = {r["name"] for r in data["roles"]}
    assert "roleP" not in remaining_role_names
    assert "roleQ" not in remaining_role_names
    assert "roleR" in remaining_role_names
    assert len(remaining_role_names) == 1

    # Verify in DB
    updated_user = crud.get_user_by_id(db_session, target_user.id)
    assert len(updated_user.roles) == 1
    assert {r.name for r in updated_user.roles} == {"roleR"}

    # Test removing a role that is not assigned
    response = client.delete(
        f"/auth/users/{target_user.id}/roles/",
        json={"role_names": ["roleP"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == f"Role 'roleP' is not assigned to user {target_user.id}"

    # Test removing roles from a non-existent user
    response = client.delete(
        "/auth/users/9999/roles/",
        json={"role_names": ["roleR"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    # Test removing roles without admin permissions
    normal_user = crud.create_user(db_session, schemas.UserCreate(email="normal_remove@example.com", password="password123"))
    normal_login_response = client.post(
        "/auth/login",
        data={"username": "normal_remove@example.com", "password": "password123"}
    )
    normal_token = normal_login_response.json()["access_token"]

    response = client.delete(
        f"/auth/users/{target_user.id}/roles/",
        json={"role_names": ["roleR"]},
        headers={"Authorization": f"Bearer {normal_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"
