# FreelanceFlow

Welcome to **FreelanceFlow**, a modern and comprehensive dashboard built for freelancers to seamlessly manage their entire workflow. Designed with a sleek, dark-themed premium UI, this project allows you to stay on top of your projects, clients, daily tasks, and tracked time all in one unified platform.

Whether you are tracking billable hours or mapping out project timelines, FreelanceFlow keeps everything organized and instantly accessible.

---

## 🌟 Live Demo

The project is configured for deployment on Vercel. You can view the live demo here:

**[[▶ Live Demo on Vercel](https://freelance-flow-rose.vercel.app/login)]**

If you are a reviewer, you can log in using the demo credentials provided right under the sign-in fields on the login page!

---

## 🛠️ Tech Stack

This project uses a modern, performant web stack:

- **Frontend:** React (powered by Vite)
- **Styling:** Vanilla CSS (Custom Design System with a sleek "Zinc" dark theme)
- **Icons:** Lucide React
- **Backend:** FastAPI (Python)
- **Database:** SQLite (managed via SQLAlchemy)
- **Authentication:** JWT and Bcrypt
- **Deployment Ready:** Vercel (Frontend & Serverless deployment integration)

---

## 💻 How to Run Locally

To get the application up and running on your local machine, follow these steps:

### Requirements

- **Node.js** (v16+ recommended)
- **Python** (v3.9+ recommended)

### 1. Setup the Backend (FastAPI)

Open a terminal and navigate to the `server` directory:

```bash
cd server
python -m venv venv

# Activate the virtual environment:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

### 2. Setup the Frontend (React + Vite)

Open a separate terminal and navigate to the `client` directory:

```bash
cd client

# Install dependencies:
npm install

# Start the development server:
npm run dev
```

The frontend will typically run on `http://localhost:5173`. Open this URL in your browser to view the app!

---

## 📂 Project Structure

```text
Freelance Manager/
├── client/                 # React Frontend
│   ├── public/             # Static assets
│   ├── src/            
│   │   ├── components/     # Reusable UI components
│   │   ├── context/        # React Context (Auth)
│   │   ├── pages/          # Application views (Dashboard, Login, Clients, etc.)
│   │   ├── App.jsx         # Main routing
│   │   └── index.css       # Core design system and theme styles
│   ├── package.json    
│   └── vite.config.js      # Vite build configuration
│
├── server/                 # FastAPI Backend
│   ├── models/             # SQLAlchemy database models
│   ├── routes/             # API endpoints (Auth, Projects, Clients, etc.)
│   ├── schemas/            # Pydantic validation schemas
│   ├── seeds/              # Database seeding scripts (Demo data generation)
│   ├── utils/              # Helper functions
│   ├── database.py         # DB connection setup
│   └── main.py             # Application entry point
│
├── freelancer.db           # SQLite database file (contains prepopulated demo data)
├── PRD.md                  # Project planning 
└── README.md               # You are here!
```

---

## 🚀 Key Features

* **Real-time Dashboard:** A centralized look at your tasks for today, active projects, and financial health.
* **Client & Project Management:** Beautifully integrated systems to track what belongs to whom.
* **Built-in Time Tracking:** Keep a precise record of how much time you are dedicating to tasks, complete with easily togglable play/pause functionality.
* **Reviewer & Demo Ready:** Comes pre-seeded with populated data and simple one-click copy demonstration credentials so anybody can navigate the complete platform.
* **Fully Responsive:** Smooth and clean mobile experience utilizing modern grid, flexbox and accordion designs.

---

## 🔮 Future Roadmap and Additions

While FreelanceFlow is fully functional, here is what we are thinking about adding next to make this the ultimate suite for freelance professionals:

1. **Automated Billing & Invoicing System:** Automatically convert tracked billable hours into beautiful, exportable PDF invoices and connect out-of-the-box payment integrations (like Stripe) to get paid directly.
2. **Third-party Integrations:** Sync daily tasks directly to Google Calendar, Slack, or Discord to unify all workflows.
3. **Advanced Analytics & Reporting:** Track month-over-month earnings and client drop-off rates with engaging charts (Chart.js or Recharts).
4. **Client Portals:** Give clients read-only access links so they can track the progress of their projects and tasks without bothering you for updates.

---

*Thank you for reviewing FreelanceFlow! If you encounter any bugs during testing, feel free to submit an issue or reach out directly.*
