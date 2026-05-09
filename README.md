# Automate Leave Management

Automate Leave Management is a full-stack leave management application with an agentic AI employee assistant and a manager review dashboard. Employees can register, log in, create chat sessions, request leave through a guided conversational workflow, and submit leave requests with AI-generated work-impact analysis. Managers can review pending requests, inspect the AI recommendation, and approve or reject leave.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Agentic Capabilities](#agentic-capabilities)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Running the Application](#running-the-application)
- [Frontend Routes](#frontend-routes)
- [Development Notes](#development-notes)
- [Troubleshooting](#troubleshooting)

## Overview

The application is designed around two main roles:

- **Employee**: uses a chat interface to apply for leave.
- **Manager**: uses a dashboard to review leave requests submitted by their team.

The employee leave request process is powered by an agentic LangGraph workflow using Gemini through LangChain. Instead of only answering a single prompt, the AI assistant manages a multi-step task: it collects leave dates, validates business rules, asks follow-up questions, checks leave balance, refines the leave reason, evaluates work impact, creates a final preview, and submits the request only after explicit employee confirmation.

The manager dashboard displays each pending leave request with employee details, leave dates, reason, AI recommendation, risk level, blockers, and suggestions.

## Features

### Authentication

- User registration with role selection.
- Employee registration can be linked to a manager.
- Login with secure password hashing.
- JWT token stored in an HTTP-only cookie.
- Current-user lookup through `/auth/me`.
- Logout by clearing the auth cookie.
- Protected frontend routes based on user role.

### Employee Chat

- Create multiple chat sessions.
- View previous chat sessions.
- Send and receive messages inside a selected chat.
- Persist chat messages in the database.
- Use an agentic LangGraph workflow to guide leave applications.

### AI Leave Request Flow

The AI workflow helps employees complete a leave request step by step:

1. Ask for leave start and end dates.
2. Extract and normalize dates from natural language.
3. Reject past dates, invalid ranges, and overlapping existing leave.
4. Calculate working days.
5. Ask for leave type: casual, sick, or privilege.
6. Check the employee's available leave balance.
7. Ask for the leave reason.
8. Rewrite the reason professionally.
9. Ask the employee to approve or revise the rewritten reason.
10. Analyze work impact using tasks, deadlines, and team leave context.
11. Show final request preview.
12. Submit or cancel the leave request.

### Manager Dashboard

- View pending leave requests from employees assigned to the logged-in manager.
- See AI recommendation: `APPROVE`, `REJECT`, or `NEEDS_REVIEW`.
- See risk level: `LOW`, `MEDIUM`, or `HIGH`.
- Review AI-generated reasoning, blockers, and suggestions.
- Approve or reject requests.
- Automatically log manager decisions.
- Deduct leave balance when a request is approved.

### Leave Management

- Default yearly leave balances:
  - Casual: 8 days
  - Sick: 10 days
  - Privilege: 12 days
- Prevents duplicate overlapping leave requests.
- Stores leave approval history.
- Supports task and project deadline data for AI risk analysis.

## Agentic Capabilities

This project includes an AI agent workflow for leave management. The agent is not just a chatbot response layer; it is a stateful process that plans the next step, asks for missing information, calls backend logic, validates constraints, produces structured decisions, and writes the final leave request to the database.

### Stateful Conversation

- Each employee chat session has a unique `thread_id`.
- LangGraph checkpointing stores the workflow state in PostgreSQL.
- The assistant remembers which step the employee is currently in, such as date collection, leave-type selection, reason approval, or final confirmation.
- Employees can complete the leave request over multiple turns instead of providing all details at once.

### Multi-Step Reasoning Flow

The agent follows a controlled graph rather than a single open-ended prompt:

1. Collect dates.
2. Extract dates from natural language.
3. Validate date ranges.
4. Check overlapping leave requests.
5. Ask for leave type.
6. Check leave balance.
7. Collect and polish the leave reason.
8. Wait for employee approval of the polished reason.
9. Analyze work impact.
10. Generate a final preview.
11. Submit or cancel based on confirmation.

### Tool-Like Backend Actions

During the workflow, the agent uses backend functions and database queries as tools:

- Checks existing leave requests for the employee.
- Reads leave balances and creates yearly balances when needed.
- Fetches active tasks in the requested leave window.
- Fetches project deadlines in the requested leave window.
- Fetches approved teammate leave under the same manager.
- Creates the final `LeaveRequest` record after confirmation.

### Structured AI Decisions

For manager-facing analysis, the agent asks the LLM for structured output instead of free-form text. The output includes:

- `recommendation`: `APPROVE`, `REJECT`, or `NEEDS_REVIEW`
- `risk_level`: `LOW`, `MEDIUM`, or `HIGH`
- `reason`: short explanation for the manager
- `blocking_items`: task or deadline titles that may block approval
- `suggestion`: recommended handover, delegation, or rescheduling action

These values are stored with the leave request and shown in the manager dashboard.

### Human-in-the-Loop Control

The employee remains in control of submission:

- The agent rewrites the leave reason professionally.
- The employee must approve the rewritten reason or provide a better one.
- The agent shows a final request preview before submission.
- The request is only saved after the employee confirms.

The manager also remains the final decision-maker:

- AI analysis supports the decision.
- Approval or rejection is performed by the manager.
- Approved requests deduct leave balance only after manager action.

### Business-Aware Risk Analysis

The agent evaluates leave impact using leave policy and delivery context:

- High-priority unfinished tasks can increase risk.
- Project deadlines inside the leave period can block approval.
- Multiple teammates already on leave can increase team risk.
- Nearly completed high-priority work can be marked for review instead of automatic rejection.

This makes the assistant useful for operational decision support, not just conversational form filling.

## Tech Stack

### Frontend

- React 19
- Vite 7
- React Router
- TanStack React Query
- Axios
- Tailwind CSS

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Uvicorn
- Passlib bcrypt password hashing
- python-jose JWT authentication
- python-dotenv

### AI and Workflow

- LangGraph
- LangChain
- Google Gemini via `langchain-google-genai`
- LangGraph PostgreSQL checkpointing
- LangSmith dependency included for tracing/testing support

## Project Structure

```text
AutomateLeaveManagement/
  backend/
    app/
      auth/
        routes.py          # Register, login, logout, current user
        utils.py           # Password hashing and JWT creation
      chat/
        routes.py          # Chat session and message endpoints
        service.py         # Chat persistence and graph invocation
      crud/
        routes.py          # User helper routes such as manager listing
      graph/
        builder.py         # Main LangGraph leave workflow
        leave_nodes.py     # Date and leave-type graph nodes
        runtime.py         # Graph runtime and PostgreSQL checkpointer
      leave/
        service.py         # Leave balance and request creation logic
      manager/
        routes.py          # Manager leave review endpoints
      models/
        user.py            # User model
        chat.py            # Chat session and message models
        leave.py           # Leave, approval, balance, task, deadline models
      schemas/
        auth.py            # Auth request schemas
        chat.py            # Chat message schema
      db.py                # Database engine/session setup
      llm_config.py        # Gemini model fallback configuration
      main.py              # FastAPI app entry point
    requirements.txt

  client/
    src/
      api/                 # Axios client and API wrappers
      components/          # Protected route component
      context/             # Auth context
      pages/               # Login, register, chat, manager dashboard
      App.jsx              # Frontend routes
      main.jsx             # React entry point
      index.css            # Tailwind/global styles
    package.json
    vite.config.js

  README.md
  LICENSE
```

## How It Works

### Authentication Flow

1. A user registers with name, email, password, role, and optionally a manager.
2. Passwords are hashed before storage.
3. On login, the backend creates a JWT containing the user's ID.
4. The JWT is stored in an HTTP-only `access_token` cookie.
5. Protected backend routes read the cookie and decode the token to identify the current user.
6. The React app calls `/auth/me` to restore the logged-in user on page load.

### Employee Leave Flow

1. The employee opens `/chat`.
2. The employee creates or selects a chat session.
3. Messages are sent to `/chats/{chat_id}/message`.
4. The backend saves the user message.
5. The LangGraph workflow processes the message.
6. The graph stores conversation state using PostgreSQL checkpointing.
7. The backend saves the assistant response.
8. When the user confirms the final preview, a `LeaveRequest` is created with AI analysis fields.

### AI Work-Impact Analysis

The graph checks:

- The employee's active tasks during the requested leave window.
- Project deadlines assigned to the employee during the leave window.
- Approved leave by teammates under the same manager.
- Task priority and progress.

The AI returns structured output containing:

- Recommendation
- Risk level
- Plain-language reason
- Blocking items
- Suggested action

This information is stored with the leave request and shown to the manager.

### Manager Decision Flow

1. A manager logs in and is redirected to `/manager`.
2. The frontend fetches `/manager/leave-requests`.
3. The backend returns pending requests for employees whose `manager_id` matches the logged-in manager.
4. The manager approves or rejects a request.
5. The backend records the decision in `leave_approvals`.
6. If approved, the employee's leave balance is reduced.

## Database Models

### User

Stores account and role information.

- `id`
- `name`
- `email`
- `password_hash`
- `role`
- `manager_id`

### ChatSession

Stores one chat thread per employee conversation.

- `id`
- `user_id`
- `thread_id`
- `title`
- `created_at`

### ChatMessage

Stores user and assistant messages.

- `id`
- `chat_id`
- `role`
- `content`
- `created_at`

### LeaveRequest

Stores submitted leave requests and AI analysis.

- `id`
- `employee_id`
- `leave_type`
- `start_date`
- `end_date`
- `reason`
- `status`
- `ai_recommendation`
- `ai_risk`
- `ai_reason`
- `ai_blockers`
- `ai_suggestion`
- `manager_warning`
- `created_at`

### LeaveApproval

Stores manager decision history.

- `id`
- `leave_request_id`
- `decided_by`
- `decision`
- `reason`
- `decided_at`

### LeaveBalance

Stores yearly leave balances.

- `id`
- `employee_id`
- `year`
- `casual`
- `sick`
- `privilege`

### ProjectDeadline

Stores employee project deadlines used during leave analysis.

- `id`
- `title`
- `description`
- `manager_id`
- `employee_id`
- `deadline_date`
- `created_at`

### Task

Stores employee tasks used during leave analysis.

- `id`
- `employee_id`
- `project_deadline_id`
- `title`
- `priority`
- `deadline`
- `progress`
- `status`
- `created_at`

## API Endpoints

### Auth

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Log in and set auth cookie |
| `GET` | `/auth/me` | Return the logged-in user |
| `POST` | `/auth/logout` | Clear auth cookie |

### Users

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/users/managers` | Return all users with manager role |

### Chats

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/chats` | Create a chat session |
| `GET` | `/chats` | List current user's chat sessions |
| `POST` | `/chats/{chat_id}/message` | Send a chat message to the AI workflow |
| `GET` | `/chats/{chat_id}/messages` | List messages in a chat session |

### Manager

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/manager/leave-requests` | List pending leave requests for the manager's team |
| `PATCH` | `/manager/leave-requests/{leave_id}/decision` | Approve or reject a leave request |

### Root

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | API health check |

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/automate_leave_management
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
GOOGLE_API_KEY=your-google-gemini-api-key
```

Create a `.env` file in the `client/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Notes:

- `DATABASE_URL` is used by SQLAlchemy and LangGraph checkpointing.
- `SECRET_KEY` and `ALGORITHM` are required for JWT creation and decoding.
- `GOOGLE_API_KEY` is required by `langchain-google-genai`.
- The backend currently allows CORS from `http://localhost:5173`.

## Local Setup

### Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer
- PostgreSQL
- Google Gemini API key

### Backend Setup

From the project root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create the PostgreSQL database:

```sql
CREATE DATABASE automate_leave_management;
```

Then create `backend/.env` using the example above.

The FastAPI app creates tables automatically on startup through `Base.metadata.create_all(bind=engine)`.

### Frontend Setup

From the project root:

```bash
cd client
npm install
```

Then create `client/.env` using the example above.

## Running the Application

### Start Backend

From `backend/`:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

FastAPI docs:

```text
http://localhost:8000/docs
```

### Start Frontend

From `client/`:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## Frontend Routes

| Route | Description | Access |
| --- | --- | --- |
| `/login` | Login page | Public |
| `/register` | Registration page | Public |
| `/chat` | Employee chat interface | Employee |
| `/manager` | Manager dashboard | Manager |
| `/` | Redirects to `/chat` | Protected by final route |

## Development Notes

- The frontend uses Axios with `withCredentials: true`, so cookies are sent with API requests.
- The backend cookie is currently configured with `secure=False`, which is suitable for local development only.
- The LangGraph runtime uses PostgreSQL checkpointing through `PostgresSaver`.
- The graph uses Gemini model fallbacks in this order:
  - `gemini-2.5-flash`
  - `gemini-2.5-flash-lite`
  - `gemini-2.0-flash`
  - `gemini-2.0-flash-lite`
- Leave balances are created lazily when an employee first needs a balance.
- Manager approval deducts leave days from the appropriate leave balance.
- The manager dashboard currently focuses on pending leave requests.

## Troubleshooting

### Frontend cannot call backend

Check that:

- `client/.env` contains `VITE_API_BASE_URL=http://localhost:8000`.
- The backend is running on port `8000`.
- The frontend is running on `http://localhost:5173`.
- CORS origins in `backend/app/main.py` include the frontend URL.

### Login works but protected pages redirect to login

Check that:

- The browser accepts cookies from the backend.
- Axios is configured with `withCredentials: true`.
- `SECRET_KEY` and `ALGORITHM` are set in `backend/.env`.

### AI chat fails

Check that:

- `GOOGLE_API_KEY` is set.
- The database is reachable.
- LangGraph checkpoint tables can be created.
- The backend logs do not show quota or service errors from Gemini.

### Database connection fails

Check that:

- PostgreSQL is running.
- `DATABASE_URL` points to an existing database.
- The username and password are correct.
- The database user has permission to create tables.

## License

This project includes a `LICENSE` file in the repository root.
