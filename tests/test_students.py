import pytest

@pytest.fixture
def admin_token(client):
    client.post(
        "/auth/register",
        json={"username": "admin_student", "email": "admin_st@example.com", "password": "pass", "role": "admin"}
    )
    response = client.post("/auth/login", data={"username": "admin_student", "password": "pass"})
    return response.json()["access_token"]

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def student_user_and_token(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "student1", 
            "email": "student1@example.com", 
            "password": "pass", 
            "role": "student",
            "student": {"name": "Student One", "email": "student1@example.com", "department": "CS", "gpa": 3.8}
        }
    )
    login_response = client.post("/auth/login", data={"username": "student1", "password": "pass"})
    return register_response.json(), login_response.json()["access_token"]

@pytest.fixture
def student_headers(student_user_and_token):
    _, token = student_user_and_token
    return {"Authorization": f"Bearer {token}"}

def test_admin_create_student(client, admin_headers):
    response = client.post(
        "/students/",
        headers=admin_headers,
        json={"name": "New Student", "email": "new@example.com", "department": "IT", "gpa": 3.5}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Student"
    assert data["email"] == "new@example.com"
    assert data["department"] == "IT"
    assert data["gpa"] == 3.5
    assert "id" in data

def test_student_cannot_create_student(client, student_headers):
    response = client.post(
        "/students/",
        headers=student_headers,
        json={"name": "Hacker", "email": "hack@example.com", "department": "IT", "gpa": 4.0}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied: admin role required"

def test_admin_get_all_students(client, admin_headers):
    client.post(
        "/students/",
        headers=admin_headers,
        json={"name": "S1", "email": "s1@example.com", "department": "IS", "gpa": 3.0}
    )
    response = client.get("/students/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_student_cannot_get_all_students(client, student_headers):
    response = client.get("/students/", headers=student_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied: admin role required"

def test_admin_get_student_by_id(client, admin_headers):
    create_response = client.post(
        "/students/",
        headers=admin_headers,
        json={"name": "S2", "email": "s2@example.com", "department": "CS", "gpa": 3.2}
    )
    student_id = create_response.json()["id"]
    response = client.get(f"/students/{student_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "S2"

def test_student_get_own_profile(client, student_headers, student_user_and_token):
    user_data, _ = student_user_and_token
    response = client.get("/students/me", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Student One"

def test_student_update_own_profile(client, student_headers):
    response = client.put(
        "/students/me",
        headers=student_headers,
        json={"department": "Software Engineering"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "Software Engineering"
    assert data["name"] == "Student One" # Other fields remain unchanged

def test_admin_delete_student(client, admin_headers):
    create_response = client.post(
        "/students/",
        headers=admin_headers,
        json={"name": "S3", "email": "s3@example.com", "department": "Math", "gpa": 2.5}
    )
    student_id = create_response.json()["id"]
    response = client.delete(f"/students/{student_id}", headers=admin_headers)
    assert response.status_code == 200
    
    # Verify deletion
    get_response = client.get(f"/students/{student_id}", headers=admin_headers)
    assert get_response.status_code == 404

def test_student_cannot_delete_student(client, student_headers):
    response = client.delete("/students/1", headers=student_headers)
    assert response.status_code == 403

def test_create_student_invalid_data(client, admin_headers):
    # Missing required field like 'name'
    response = client.post(
        "/students/",
        headers=admin_headers,
        json={"email": "invalid@example.com", "department": "CS"}
    )
    assert response.status_code == 422 # Validation Error

def test_get_nonexistent_student(client, admin_headers):
    response = client.get("/students/9999", headers=admin_headers)
    assert response.status_code == 404
