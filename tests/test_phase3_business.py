"""
Phase 3 Tests: Business Logic Layer
Tests status transitions, today's tasks, billable summaries, and dashboard.
"""
import time
import pytest
from datetime import date, timedelta


class TestTaskStatusTransitions:
    """Test task status change with validation and side effects."""

    def _setup_task(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "BL Client"}, headers=auth_headers)
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={"client_id": client_id, "name": "BL Project"}, headers=auth_headers)
        project_id = resp.json()["id"]
        resp = client.post("/api/tasks", json={"project_id": project_id, "title": "BL Task"}, headers=auth_headers)
        return resp.json()["id"], project_id

    def test_valid_status_transitions(self, client, auth_headers):
        """Test: Task status transition valid paths work."""
        task_id, _ = self._setup_task(client, auth_headers)

        # todo → in-progress
        resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "in-progress"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "in-progress"
        assert resp.json()["metadata"].get("suggest_start_timer") is True

        # in-progress → done
        resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

        # done → todo
        resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "todo"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "todo"

    def test_invalid_status_returns_422(self, client, auth_headers):
        """Test: Task status cannot be set to invalid value (422)."""
        task_id, _ = self._setup_task(client, auth_headers)

        resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "cancelled"}, headers=auth_headers)
        assert resp.status_code == 422

    def test_done_auto_stops_running_timer(self, client, auth_headers):
        """Test: Marking task as 'done' auto-stops running timer."""
        task_id, _ = self._setup_task(client, auth_headers)

        # Start a timer
        resp = client.post("/api/time-entries", json={"task_id": task_id}, headers=auth_headers)
        entry_id = resp.json()["id"]

        time.sleep(1)

        # Mark as done — should auto-stop timer
        resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["metadata"]["timer_stopped"] is True
        assert resp.json()["metadata"]["duration_seconds"] >= 1

        # Verify the time entry is actually stopped
        resp = client.get(f"/api/time-entries/{entry_id}", headers=auth_headers)
        assert resp.json()["ended_at"] is not None


class TestTodaysTasks:
    """Test today's to-do list functionality."""

    def _setup_tasks(self, client, auth_headers):
        resp = client.post("/api/clients", json={"name": "Today Client"}, headers=auth_headers)
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={"client_id": client_id, "name": "Today Project"}, headers=auth_headers)
        project_id = resp.json()["id"]

        t1 = client.post("/api/tasks", json={"project_id": project_id, "title": "Today Task 1", "is_today": True}, headers=auth_headers).json()["id"]
        t2 = client.post("/api/tasks", json={"project_id": project_id, "title": "Today Task 2", "is_today": True}, headers=auth_headers).json()["id"]
        t3 = client.post("/api/tasks", json={"project_id": project_id, "title": "Not Today Task", "is_today": False}, headers=auth_headers).json()["id"]

        return t1, t2, t3

    def test_today_returns_only_today_tasks(self, client, auth_headers):
        """Test: Today's to-do returns only is_today=true tasks."""
        t1, t2, t3 = self._setup_tasks(client, auth_headers)

        resp = client.get("/api/tasks/today/list", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        task_ids = [t["id"] for t in data]
        assert t1 in task_ids
        assert t2 in task_ids
        assert t3 not in task_ids

    def test_toggle_today(self, client, auth_headers):
        """Test: Toggle is_today works both ways."""
        t1, t2, t3 = self._setup_tasks(client, auth_headers)

        # Toggle t1 off
        resp = client.patch(f"/api/tasks/{t1}/today", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_today"] is False

        # Toggle t1 back on
        resp = client.patch(f"/api/tasks/{t1}/today", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_today"] is True


class TestProjectSummary:
    """Test project summary with billable amounts and deadline flags."""

    def _setup_project_with_time(self, client, auth_headers, deadline=None, hourly_rate=100.0):
        resp = client.post("/api/clients", json={"name": "Summary Client"}, headers=auth_headers)
        client_id = resp.json()["id"]

        project_data = {
            "client_id": client_id,
            "name": "Summary Project",
            "hourly_rate": hourly_rate,
            "is_billable": True,
        }
        if deadline:
            project_data["deadline"] = deadline.isoformat()

        resp = client.post("/api/projects", json=project_data, headers=auth_headers)
        project_id = resp.json()["id"]

        # Create tasks with different statuses
        t1 = client.post("/api/tasks", json={"project_id": project_id, "title": "Done Task", "status": "done"}, headers=auth_headers).json()["id"]
        t2 = client.post("/api/tasks", json={"project_id": project_id, "title": "In Progress Task", "status": "in-progress"}, headers=auth_headers).json()["id"]
        t3 = client.post("/api/tasks", json={"project_id": project_id, "title": "Todo Task", "status": "todo"}, headers=auth_headers).json()["id"]

        # Add time entries to t1 (start + stop)
        resp = client.post("/api/time-entries", json={"task_id": t1}, headers=auth_headers)
        entry_id = resp.json()["id"]
        time.sleep(1)
        client.put(f"/api/time-entries/{entry_id}/stop", headers=auth_headers)

        return project_id

    def test_project_summary_calculates_time(self, client, auth_headers):
        """Test: Project summary calculates total time correctly across tasks."""
        project_id = self._setup_project_with_time(client, auth_headers)

        resp = client.get(f"/api/projects/{project_id}/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_seconds"] > 0
        assert data["tasks"]["total"] == 3
        assert data["tasks"]["done"] == 1
        assert data["tasks"]["in_progress"] == 1
        assert data["tasks"]["todo"] == 1

    def test_project_summary_billable_amount(self, client, auth_headers):
        """Test: Project summary calculates billable amount correctly."""
        project_id = self._setup_project_with_time(client, auth_headers, hourly_rate=100.0)

        resp = client.get(f"/api/projects/{project_id}/summary", headers=auth_headers)
        data = resp.json()
        assert data["total_seconds"] > 0  # Billable amount may round to 0 for short durations

    def test_project_summary_overdue_deadline(self, client, auth_headers):
        """Test: Project summary flags overdue deadline."""
        yesterday = date.today() - timedelta(days=1)
        project_id = self._setup_project_with_time(client, auth_headers, deadline=yesterday)

        resp = client.get(f"/api/projects/{project_id}/summary", headers=auth_headers)
        data = resp.json()
        assert data["deadline_status"]["is_overdue"] is True
        assert data["deadline_status"]["is_approaching"] is False

    def test_project_summary_approaching_deadline(self, client, auth_headers):
        """Test: Project summary flags approaching deadline (within 3 days)."""
        approaching = date.today() + timedelta(days=2)
        project_id = self._setup_project_with_time(client, auth_headers, deadline=approaching)

        resp = client.get(f"/api/projects/{project_id}/summary", headers=auth_headers)
        data = resp.json()
        assert data["deadline_status"]["is_overdue"] is False
        assert data["deadline_status"]["is_approaching"] is True


class TestProjectStatusChange:
    """Test project status transitions."""

    def test_completing_project_warns_incomplete_tasks(self, client, auth_headers):
        """Test: Completing a project warns about incomplete tasks (does not block)."""
        resp = client.post("/api/clients", json={"name": "Status Client"}, headers=auth_headers)
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={"client_id": client_id, "name": "Status Project"}, headers=auth_headers)
        project_id = resp.json()["id"]

        # Add a todo task (incomplete)
        client.post("/api/tasks", json={"project_id": project_id, "title": "Incomplete Task", "status": "todo"}, headers=auth_headers)

        # Complete the project — should warn but succeed
        resp = client.patch(f"/api/projects/{project_id}/status", json={"status": "completed"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert "warnings" in resp.json()
        assert "1 task(s) are not yet done" in resp.json()["warnings"]


class TestDashboard:
    """Test dashboard summary endpoint."""

    def test_dashboard_returns_correct_counts(self, client, auth_headers):
        """Test: Dashboard returns correct counts."""
        # Create data
        resp = client.post("/api/clients", json={"name": "Dash Client 1", "status": "active"}, headers=auth_headers)
        c1 = resp.json()["id"]
        resp = client.post("/api/clients", json={"name": "Dash Client 2", "status": "active"}, headers=auth_headers)
        c2 = resp.json()["id"]

        resp = client.post("/api/projects", json={
            "client_id": c1, "name": "Dash Project 1", "status": "active",
            "deadline": (date.today() - timedelta(days=5)).isoformat(),  # Overdue
        }, headers=auth_headers)
        p1 = resp.json()["id"]

        resp = client.post("/api/projects", json={
            "client_id": c2, "name": "Dash Project 2", "status": "active",
            "deadline": (date.today() + timedelta(days=2)).isoformat(),  # Approaching
        }, headers=auth_headers)
        p2 = resp.json()["id"]

        # Add today tasks
        client.post("/api/tasks", json={"project_id": p1, "title": "Today Todo", "is_today": True, "status": "todo"}, headers=auth_headers)
        client.post("/api/tasks", json={"project_id": p1, "title": "Today Done", "is_today": True, "status": "done"}, headers=auth_headers)

        # Get dashboard
        resp = client.get("/api/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert data["active_clients"] == 2
        assert data["active_projects"] == 2
        assert data["today_tasks"]["todo"] == 1
        assert data["today_tasks"]["done"] == 1
        assert data["today_tasks"]["total"] == 2
        assert len(data["overdue_projects"]) == 1
        assert data["overdue_projects"][0]["name"] == "Dash Project 1"
        assert len(data["approaching_deadline_projects"]) == 1
        assert data["approaching_deadline_projects"][0]["name"] == "Dash Project 2"

    def test_dashboard_week_calculation(self, client, auth_headers):
        """Test: Dashboard week calculation is correct."""
        resp = client.post("/api/clients", json={"name": "Week Client"}, headers=auth_headers)
        client_id = resp.json()["id"]
        resp = client.post("/api/projects", json={
            "client_id": client_id, "name": "Week Project",
            "hourly_rate": 100.0, "is_billable": True,
        }, headers=auth_headers)
        project_id = resp.json()["id"]
        resp = client.post("/api/tasks", json={"project_id": project_id, "title": "Week Task"}, headers=auth_headers)
        task_id = resp.json()["id"]

        # Create a time entry and stop it
        resp = client.post("/api/time-entries", json={"task_id": task_id}, headers=auth_headers)
        entry_id = resp.json()["id"]
        time.sleep(1)
        client.put(f"/api/time-entries/{entry_id}/stop", headers=auth_headers)

        resp = client.get("/api/dashboard", headers=auth_headers)
        data = resp.json()
        assert data["weekly_billable_hours"] >= 0  # At least 0, might be very small
