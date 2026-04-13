"""
Phase 1 Tests: Database Foundation + CRUD API
Tests all CRUD operations for clients, projects, tasks, and time entries.
"""
import time
import pytest


# ═══════════════════════════════════════════════
# CLIENT CRUD TESTS
# ═══════════════════════════════════════════════

class TestClientCRUD:
    """Test: Create a client, retrieve it, verify all fields."""

    def test_create_and_retrieve_client(self, client):
        # Create
        response = client.post("/api/clients", json={
            "name": "Test Client",
            "email": "client@test.com",
            "phone": "+1-555-1234",
            "company": "Test Corp",
            "notes": "Great client",
            "status": "active",
        })
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
        response = client.get(f"/api/clients/{client_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["name"] == "Test Client"
        assert data["email"] == "client@test.com"

    def test_list_clients(self, client):
        # Create two clients
        client.post("/api/clients", json={"name": "Client A"})
        client.post("/api/clients", json={"name": "Client B"})

        response = client.get("/api/clients")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_client(self, client):
        resp = client.post("/api/clients", json={"name": "Old Name"})
        client_id = resp.json()["id"]

        response = client.put(f"/api/clients/{client_id}", json={"name": "New Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_delete_client(self, client):
        resp = client.post("/api/clients", json={"name": "To Delete"})
        client_id = resp.json()["id"]

        response = client.delete(f"/api/clients/{client_id}")
        assert response.status_code == 204

        response = client.get(f"/api/clients/{client_id}")
        assert response.status_code == 404

    def test_filter_clients_by_status(self, client):
        client.post("/api/clients", json={"name": "Active", "status": "active"})
        client.post("/api/clients", json={"name": "Inactive", "status": "inactive"})

        response = client.get("/api/clients?status=active")
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active"


# ═══════════════════════════════════════════════
# PROJECT CRUD TESTS
# ═══════════════════════════════════════════════

class TestProjectCRUD:
    """Test: Create a project linked to a client, retrieve with client info."""

    def _create_client(self, client) -> str:
        resp = client.post("/api/clients", json={"name": "Project Test Client"})
        return resp.json()["id"]

    def test_create_project_with_client(self, client):
        client_id = self._create_client(client)

        response = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Test Project",
            "description": "A test project",
            "hourly_rate": 85.0,
            "is_billable": True,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["client_id"] == client_id
        assert data["client_name"] == "Project Test Client"
        assert data["hourly_rate"] == 85.0
        assert data["is_billable"] is True
        assert data["status"] == "active"

    def test_cannot_create_project_with_nonexistent_client(self, client):
        """Test: Cannot create a project with non-existent client_id (404)."""
        response = client.post("/api/projects", json={
            "client_id": "00000000-0000-0000-0000-000000000000",
            "name": "Bad Project",
        })
        assert response.status_code == 404

    def test_list_projects_with_client_filter(self, client):
        client_id = self._create_client(client)
        client.post("/api/projects", json={"client_id": client_id, "name": "P1"})
        client.post("/api/projects", json={"client_id": client_id, "name": "P2"})

        response = client.get(f"/api/projects?client_id={client_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2


# ═══════════════════════════════════════════════
# TASK CRUD TESTS
# ═══════════════════════════════════════════════

class TestTaskCRUD:
    """Test: Create a task linked to a project, retrieve with project info."""

    def _create_client_and_project(self, client):
        resp = client.post("/api/clients", json={"name": "Task Test Client"})
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Task Test Project",
        })
        return resp.json()["id"]

    def test_create_task_with_project(self, client):
        project_id = self._create_client_and_project(client)

        response = client.post("/api/tasks", json={
            "project_id": project_id,
            "title": "Test Task",
            "description": "A test task",
            "priority": "high",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["project_id"] == project_id
        assert data["project_name"] == "Task Test Project"
        assert data["priority"] == "high"
        assert data["status"] == "todo"

    def test_cannot_create_task_with_nonexistent_project(self, client):
        """Test: Cannot create a task with non-existent project_id (404)."""
        response = client.post("/api/tasks", json={
            "project_id": "00000000-0000-0000-0000-000000000000",
            "title": "Bad Task",
        })
        assert response.status_code == 404


# ═══════════════════════════════════════════════
# TIME ENTRY / TIMER TESTS
# ═══════════════════════════════════════════════

class TestTimeEntries:
    """Test: Start a timer, stop it, verify duration_seconds is correct."""

    def _create_task(self, client):
        resp = client.post("/api/clients", json={"name": "Timer Client"})
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Timer Project",
        })
        project_id = resp.json()["id"]
        resp = client.post("/api/tasks", json={
            "project_id": project_id,
            "title": "Timer Task",
        })
        return resp.json()["id"]

    def test_start_and_stop_timer(self, client):
        task_id = self._create_task(client)

        # Start timer
        response = client.post("/api/time-entries", json={"task_id": task_id})
        assert response.status_code == 201
        data = response.json()
        assert data["ended_at"] is None
        assert data["duration_seconds"] is None
        entry_id = data["id"]

        # Brief pause to get measurable duration
        time.sleep(1)

        # Stop timer
        response = client.put(f"/api/time-entries/{entry_id}/stop", json={"note": "Done"})
        assert response.status_code == 200
        data = response.json()
        assert data["ended_at"] is not None
        assert data["duration_seconds"] is not None
        assert data["duration_seconds"] >= 1
        assert data["note"] == "Done"

    def test_cannot_start_duplicate_timer(self, client):
        task_id = self._create_task(client)

        # Start first timer
        client.post("/api/time-entries", json={"task_id": task_id})

        # Try to start second timer on same task
        response = client.post("/api/time-entries", json={"task_id": task_id})
        assert response.status_code == 409

    def test_task_summary_with_time(self, client):
        task_id = self._create_task(client)

        # Start and stop a timer
        resp = client.post("/api/time-entries", json={"task_id": task_id})
        entry_id = resp.json()["id"]
        time.sleep(1)
        client.put(f"/api/time-entries/{entry_id}/stop")

        # Check task summary
        response = client.get(f"/api/tasks/{task_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_time_spent"] >= 1
        assert data["time_entry_count"] == 1


# ═══════════════════════════════════════════════
# CASCADE DELETE TESTS
# ═══════════════════════════════════════════════

class TestCascadeDelete:
    """Test: Delete a client cascades to projects and tasks."""

    def test_delete_client_cascades(self, client):
        # Create client → project → task
        resp = client.post("/api/clients", json={"name": "Cascade Client"})
        client_id = resp.json()["id"]

        resp = client.post("/api/projects", json={
            "client_id": client_id,
            "name": "Cascade Project",
        })
        project_id = resp.json()["id"]

        resp = client.post("/api/tasks", json={
            "project_id": project_id,
            "title": "Cascade Task",
        })
        task_id = resp.json()["id"]

        # Delete client
        response = client.delete(f"/api/clients/{client_id}")
        assert response.status_code == 204

        # Verify project is gone
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 404

        # Verify task is gone
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 404


# ═══════════════════════════════════════════════
# USER ISOLATION TEST
# ═══════════════════════════════════════════════

class TestUserIsolation:
    """Test: All list endpoints return only data for the test user."""

    def test_list_returns_only_user_data(self, client):
        # Create a client for the hardcoded test user
        client.post("/api/clients", json={"name": "My Client"})

        # List should return only this user's data
        response = client.get("/api/clients")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Client"
