"""
Phase 1 Tests: Database Foundation + CRUD API
Tests all CRUD operations for clients, projects, tasks, and time entries.
Now requires JWT auth (Phase 2).
"""
import time
import pytest


# ═══════════════════════════════════════════════
# CLIENT CRUD TESTS
# ═══════════════════════════════════════════════

class TestClientCRUD:
    """Test: Create a client, retrieve it, verify all fields."""

    def test_create_and_retrieve_client(self, client, auth_headers):
        # Create
        response = client.post("/api/clients", json={
            "name": "Test Client",
            "email": "client@test.com",
            "phone": "+1-555-1234",
            "company": "Test Corp",
            "notes": "Great client",
            "status": "active",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Client"
        assert data["email"] == "client@test.com"
        assert data["phone"] == "+1-555-1234"
        assert data["company"] == "Test Corp"
        assert data["notes"] == "Great client"
        assert data["status"] == "active"
        assert data["project_count"] == 0
        client_id = data["id"]

        # Retrieve
        response = client.get(f"/api/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["name"] == "Test Client"
        assert data["email"] == "client@test.com"

    def test_list_clients(self, client, auth_headers):
        client.post("/api/clients", json={"name": "Client A"}, headers=auth_headers)
        client.post("/api/clients", json={"name": "Client B"}, headers=auth_headers)

        response = client.get("/api/clients", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_client(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "Old Name"}, headers=auth_headers)
        client_id = resp.json()["id"]

        response = client.put(f"/api/clients/{client_id}", json={"name": "New Name"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_delete_client(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "To Delete"}, headers=auth_headers)
        client_id = resp.json()["id"]

        response = client.delete(f"/api/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 204

        response = client.get(f"/api/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_filter_clients_by_status(self, client, auth_headers):
        client.post("/api/clients", json={"name": "Active", "status": "active"}, headers=auth_headers)
        client.post("/api/clients", json={"name": "Inactive", "status": "inactive"}, headers=auth_headers)

        response = client.get("/api/clients?status=active", headers=auth_headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active"


# ═══════════════════════════════════════════════
# PROJECT CRUD TESTS
# ═══════════════════════════════════════════════

class TestProjectCRUD:
    """Test: Create a project linked to a client, retrieve with client info."""

    def _create_client(self, client, auth_headers) -> str:
        resp = client.post("/api/clients", json={"name": "Project Test Client"}, headers=auth_headers)
        return resp.json()["id"]

    def test_create_project_with_client(self, client, auth_headers):
        client_id = self._create_client(client, auth_headers)

        response = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Test Project",
            "description": "A test project",
            "hourly_rate": 85.0,
            "is_billable": True,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["client_id"] == client_id
        assert data["client_name"] == "Project Test Client"
        assert data["hourly_rate"] == 85.0
        assert data["is_billable"] is True
        assert data["status"] == "active"

    def test_cannot_create_project_with_nonexistent_client(self, client, auth_headers):
        """Test: Cannot create a project with non-existent client_id (404)."""
        response = client.post("/api/projects", json={
            "client_id": "00000000-0000-0000-0000-000000000000",
            "name": "Bad Project",
        }, headers=auth_headers)
        assert response.status_code == 404

    def test_list_projects_with_client_filter(self, client, auth_headers):
        client_id = self._create_client(client, auth_headers)
        client.post("/api/projects", json={"client_id": client_id, "name": "P1"}, headers=auth_headers)
        client.post("/api/projects", json={"client_id": client_id, "name": "P2"}, headers=auth_headers)

        response = client.get(f"/api/projects?client_id={client_id}", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2


# ═══════════════════════════════════════════════
# TASK CRUD TESTS
# ═══════════════════════════════════════════════

class TestTaskCRUD:
    """Test: Create a task linked to a project, retrieve with project info."""

    def _create_client_and_project(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "Task Test Client"}, headers=auth_headers)
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Task Test Project",
        }, headers=auth_headers)
        return resp.json()["id"]

    def test_create_task_with_project(self, client, auth_headers):
        project_id = self._create_client_and_project(client, auth_headers)

        response = client.post("/api/tasks", json={
            "project_id": project_id,
            "title": "Test Task",
            "description": "A test task",
            "priority": "high",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["project_id"] == project_id
        assert data["project_name"] == "Task Test Project"
        assert data["priority"] == "high"
        assert data["status"] == "todo"

    def test_cannot_create_task_with_nonexistent_project(self, client, auth_headers):
        """Test: Cannot create a task with non-existent project_id (404)."""
        response = client.post("/api/tasks", json={
            "project_id": "00000000-0000-0000-0000-000000000000",
            "title": "Bad Task",
        }, headers=auth_headers)
        assert response.status_code == 404


# ═══════════════════════════════════════════════
# TIME ENTRY / TIMER TESTS
# ═══════════════════════════════════════════════

class TestTimeEntries:
    """Test: Start a timer, stop it, verify duration_seconds is correct."""

    def _create_task(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "Timer Client"}, headers=auth_headers)
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Timer Project",
        }, headers=auth_headers)
        project_id = resp.json()["id"]
        resp = client.post("/api/tasks", json={
            "project_id": project_id,
            "title": "Timer Task",
        }, headers=auth_headers)
        return resp.json()["id"]

    def test_start_and_stop_timer(self, client, auth_headers):
        task_id = self._create_task(client, auth_headers)

        # Start timer
        response = client.post("/api/time-entries", json={"task_id": task_id}, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["ended_at"] is None
        assert data["duration_seconds"] is None
        entry_id = data["id"]

        time.sleep(1)

        # Stop timer
        response = client.put(f"/api/time-entries/{entry_id}/stop", json={"note": "Done"}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ended_at"] is not None
        assert data["duration_seconds"] is not None
        assert data["duration_seconds"] >= 1
        assert data["note"] == "Done"

    def test_cannot_start_duplicate_timer(self, client, auth_headers):
        task_id = self._create_task(client, auth_headers)

        client.post("/api/time-entries", json={"task_id": task_id}, headers=auth_headers)
        response = client.post("/api/time-entries", json={"task_id": task_id}, headers=auth_headers)
        assert response.status_code == 409

    def test_task_summary_with_time(self, client, auth_headers):
        task_id = self._create_task(client, auth_headers)

        resp = client.post("/api/time-entries", json={"task_id": task_id}, headers=auth_headers)
        entry_id = resp.json()["id"]
        time.sleep(1)
        client.put(f"/api/time-entries/{entry_id}/stop", headers=auth_headers)

        response = client.get(f"/api/tasks/{task_id}/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_time_spent"] >= 1
        assert data["time_entry_count"] == 1


# ═══════════════════════════════════════════════
# CASCADE DELETE TESTS
# ═══════════════════════════════════════════════

class TestCascadeDelete:
    """Test: Delete a client cascades to projects and tasks."""

    def test_delete_client_cascades(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "Cascade Client"}, headers=auth_headers)
        client_id = resp.json()["id"]

        resp = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Cascade Project",
        }, headers=auth_headers)
        project_id = resp.json()["id"]

        resp = client.post("/api/tasks", json={
            "project_id": project_id,
            "title": "Cascade Task",
        }, headers=auth_headers)
        task_id = resp.json()["id"]

        response = client.delete(f"/api/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 204

        response = client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 404

        response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 404


# ═══════════════════════════════════════════════
# USER ISOLATION TEST
# ═══════════════════════════════════════════════

class TestUserIsolation:
    """Test: All list endpoints return only data for the test user."""

    def test_list_returns_only_user_data(self, client, auth_headers):
        client.post("/api/clients", json={"name": "My Client"}, headers=auth_headers)

        response = client.get("/api/clients", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Client"
