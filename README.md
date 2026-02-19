🧠 MindMate

A personalized, authenticated decision-support system with memory, preferences, and feedback-driven behavior.

MindMate helps users think clearly about decisions by combining structured user memory, configurable response styles, and transparent system behavior in a persistent, multi-user environment.

🎯 Overview

MindMate is a multi-user, authenticated application that provides decision support through a conversational interface.

Unlike generic LLM usage that treats each interaction as isolated, MindMate is designed to operate as a stateful system, where responses are shaped by:

User-scoped personalization (preferences, tone, and memory)

Persistent context across sessions

Deterministic behavior controls that ensure consistency

Feedback-aware adaptation that refines how responses are delivered over time

Explainability and observability into system decisions

This allows MindMate to provide responses that are more consistent, personalized, and interpretable than standard stateless chatbot interactions.

🏗️ Architecture
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Frontend  │ ──────► │   FastAPI    │ ──────► │   LLM Provider  │
│  (Next.js)  │  HTTPS  │   Backend    │ prompt  │  (API-based)    │
│             │ ◄────── │              │ ◄────── │                 │
└─────────────┘         └──────────────┘         └─────────────────┘
           │
           ▼
   Supabase Auth & DB

Key Architectural Choices

Authentication-first design using Supabase Auth and JWT verification

User-scoped data isolation for preferences, memory, and feedback

Policy-driven response generation layered over an LLM

Deterministic control logic for tone, memory retrieval, and adaptation

🧩 Core Capabilities
1. Authentication & Multi-User Isolation

All users authenticate via Supabase (free tier)

JWTs are verified on every backend request

Preferences, memory, and feedback are strictly scoped per user

Sessions persist securely across devices and refreshes

2. Preference-Aware Responses

Users can explicitly select how MindMate responds:

Clean

Casual

Blunt

Unfiltered (explicit opt-in)

Response styles are enforced through deterministic prompt constraints, ensuring predictable and controllable behavior.

3. Structured Memory

MindMate stores structured summaries, rather than raw conversation logs, enabling reliable personalization over time.

Memory types include:

Preference memory (tone, risk tolerance)

Pattern memory (e.g., overthinking, reassurance-seeking)

Outcome memory (what advice helped or didn’t)

Each memory item includes confidence scoring, decay, and conflict handling to maintain relevance and stability.

4. Feedback-Driven Adaptation

Users can provide feedback on:

Usefulness

Tone alignment

Outcome effectiveness

Feedback is aggregated and verified before influencing behavior, allowing the system to refine how it responds while keeping underlying reasoning stable.

5. Explainability & Observability

In development mode, MindMate exposes internal metadata such as:

Response tone used

Memory references applied

Confidence estimates

This improves debugging, trust, and system transparency without exposing internals to end users.

📁 Project Structure
MindMate/
├── backend/
│   ├── auth.py               # JWT verification & auth guards
│   ├── db.py                 # Supabase anon/admin clients
│   ├── preferences.py        # User preference logic
│   ├── memory.py             # Structured memory & decay
│   ├── contradiction.py      # Conflict detection
│   ├── feedback.py           # Feedback processing
│   ├── main.py               # FastAPI app
│   └── requirements.txt
│
└── frontend/
    ├── app/
    │   ├── login/            # Auth UI
    │   ├── page.jsx          # Chat interface
    │   └── layout.jsx
    ├── components/
    │   ├── ChatInput.jsx
    │   ├── FeedbackPanel.jsx
    │   ├── ExplanationPanel.jsx (dev only)
    │   └── ToneSelector.jsx
    ├── lib/api.js             # Auth-aware API client
    └── package.json

🚀 Setup Instructions
Prerequisites

Node.js 18+

Python 3.9+

Supabase account (free tier)

Backend Setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload


Backend runs at: http://localhost:8000
API docs: http://localhost:8000/docs

Frontend Setup
cd frontend
npm install
npm run dev


Frontend runs at: http://localhost:3000

🔐 Authentication

Email/password authentication via Supabase

Tokens automatically attached to API requests

Unauthenticated users are redirected to /login

Sessions expire gracefully

🎮 Usage

Log in or sign up

Enter a decision or dilemma in chat

Select a response tone (optional)

Receive a response

Provide feedback (optional)

MindMate maintains personalized context across sessions to improve consistency and relevance.

🧪 Development & Debugging

Explanation panel available in development mode only

Logs include memory usage and policy decisions

Internal reasoning and chain-of-thought are not exposed

📦 Deployment

Frontend: Vercel (free tier)

Backend: Render (free tier)

Auth & DB: Supabase (free tier)

All external services are configured via environment variables.

🧑‍⚖️ Design Philosophy

Stability > Intelligence
Determinism > Autonomy
Explainability > Cleverness

MindMate is designed to remain reliable, debuggable, and predictable as a decision-support system.

🙏 Credits

FastAPI

Next.js

Supabase

Tailwind CSS
