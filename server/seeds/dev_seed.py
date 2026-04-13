"""
Seed script — populates dev database with test data.
1 user, 2 clients, 3 projects, 5 tasks as per PRD.

Usage: cd server && python -m seeds.dev_seed
"""
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Add server dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import SessionLocal, engine, Base
from models.user import User
from models.client import Client
from models.project import Project
from models.task import Task
from models.time_entry import TimeEntry

import models  # noqa: F401


def seed():
    """Create test data."""
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Clear existing data
        db.query(TimeEntry).delete()
        db.query(Task).delete()
        db.query(Project).delete()
        db.query(Client).delete()
        db.query(User).delete()
        db.commit()

        # --- User ---
        user = User(
            id="11111111-1111-1111-1111-111111111111",
            username="freelancer",
            email="freelancer@example.com",
            password_hash="$2b$12$placeholder_hash_not_real_but_valid_length_padding",
        )
        db.add(user)
        db.flush()

        # --- Clients ---
        client1 = Client(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="Acme Corp",
            email="contact@acme.com",
            phone="+1-555-0101",
            company="Acme Corporation",
            notes="Long-term client, web development projects",
            status="active",
        )
        client2 = Client(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="StartupXYZ",
            email="hello@startupxyz.io",
            phone="+1-555-0202",
            company="StartupXYZ Inc",
            notes="Early-stage startup, mobile app project",
            status="active",
        )
        db.add_all([client1, client2])
        db.flush()

        # --- Projects ---
        now = datetime.now(timezone.utc)
        project1 = Project(
            id=str(uuid.uuid4()),
            user_id=user.id,
            client_id=client1.id,
            name="Website Redesign",
            description="Complete redesign of the corporate website",
            status="active",
            deadline=(now + timedelta(days=14)).date(),
            hourly_rate=85.00,
            is_billable=True,
        )
        project2 = Project(
            id=str(uuid.uuid4()),
            user_id=user.id,
            client_id=client1.id,
            name="API Integration",
            description="Third-party API integration for payment processing",
            status="active",
            deadline=(now + timedelta(days=2)).date(),  # Approaching deadline
            hourly_rate=95.00,
            is_billable=True,
        )
        project3 = Project(
            id=str(uuid.uuid4()),
            user_id=user.id,
            client_id=client2.id,
            name="Mobile App MVP",
            description="React Native mobile app for iOS and Android",
            status="active",
            deadline=(now - timedelta(days=3)).date(),  # Overdue!
            hourly_rate=100.00,
            is_billable=True,
        )
        db.add_all([project1, project2, project3])
        db.flush()

        # --- Tasks ---
        task1 = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            project_id=project1.id,
            title="Design homepage mockup",
            description="Create Figma mockup for the new homepage",
            status="done",
            priority="high",
            is_today=False,
            estimated_hours=4.0,
        )
        task2 = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            project_id=project1.id,
            title="Implement responsive navigation",
            description="Build the responsive nav bar with mobile hamburger menu",
            status="in-progress",
            priority="high",
            is_today=True,
            estimated_hours=3.0,
        )
        task3 = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            project_id=project2.id,
            title="Set up Stripe SDK",
            description="Install and configure Stripe SDK for payment processing",
            status="todo",
            priority="high",
            is_today=True,
            estimated_hours=2.0,
        )
        task4 = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            project_id=project3.id,
            title="User authentication flow",
            description="Implement login/register screens with Firebase Auth",
            status="in-progress",
            priority="high",
            is_today=True,
            estimated_hours=5.0,
        )
        task5 = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            project_id=project3.id,
            title="Push notification setup",
            description="Configure push notifications for iOS and Android",
            status="todo",
            priority="medium",
            is_today=False,
            estimated_hours=3.0,
        )
        db.add_all([task1, task2, task3, task4, task5])
        db.flush()

        # --- Time Entries ---
        # Completed entry for task1
        entry1 = TimeEntry(
            user_id=user.id,
            task_id=task1.id,
            started_at=now - timedelta(hours=5),
            ended_at=now - timedelta(hours=1),
            duration_seconds=14400,  # 4 hours
            note="Completed homepage mockup design",
        )
        # Completed entry for task2
        entry2 = TimeEntry(
            user_id=user.id,
            task_id=task2.id,
            started_at=now - timedelta(hours=2),
            ended_at=now - timedelta(minutes=30),
            duration_seconds=5400,  # 1.5 hours
            note="Started responsive nav implementation",
        )
        # Running timer for task4
        entry3 = TimeEntry(
            user_id=user.id,
            task_id=task4.id,
            started_at=now - timedelta(minutes=45),
            ended_at=None,
            duration_seconds=None,
            note="Working on auth flow",
        )
        db.add_all([entry1, entry2, entry3])

        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   User: {user.username} ({user.email})")
        print(f"   Clients: {client1.name}, {client2.name}")
        print(f"   Projects: {project1.name}, {project2.name}, {project3.name}")
        print(f"   Tasks: {task1.title}, {task2.title}, {task3.title}, {task4.title}, {task5.title}")
        print(f"   Time entries: 3 (2 completed, 1 running)")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
