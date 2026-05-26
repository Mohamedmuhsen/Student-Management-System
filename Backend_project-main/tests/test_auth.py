def test_register_admin(client):
    response = client.post(
        "/auth/register",
        json={"username": "admin1", "email": "admin1@example.com", "password": "password123", "role": "admin"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "admin1"
    assert data["email"] == "admin1@example.com"
    assert data["role"] == "admin"
    assert "password" not in data

def test_register_duplicate_user(client):
    client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123", "role": "student"}
    )
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123", "role": "student"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already registered"

def test_login_success(client):
    client.post(
        "/auth/register",
        json={"username": "loginuser", "email": "login@example.com", "password": "password123", "role": "student"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={"username": "loginuser2", "email": "login2@example.com", "password": "password123", "role": "student"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "loginuser2", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        data={"username": "ghost", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
