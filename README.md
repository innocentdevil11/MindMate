🧠 MindMate

A futuristic multi-agent AI decision system powered by LangGraph, FastAPI, and Next.js.

**"A private board of AI directors helping you think clearly."**

## 🎯 Overview

MindMate provides AI-powered decision making through five specialized minds:

- **Ethical Agent**: Moral & philosophical perspective
- **Risk & Logic Agent**: Analytical risk assessment  
- **EQ Agent**: Emotional intelligence lens
- **Value Alignment Agent**: Personal values harmony
- **Red Team Agent**: Devil's advocate perspective

All perspectives are synthesized by an **Aggregator Agent** into a final council resolution.

---

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Next.js   │ ──────► │   FastAPI    │ ──────► │   LangGraph     │
│   Frontend  │  HTTP   │   Backend    │ invoke  │  Multi-Agent    │
│             │ ◄────── │              │ ◄────── │   System        │
└─────────────┘         └──────────────┘         └─────────────────┘
```

- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS, Framer Motion
- **Backend**: FastAPI with Pydantic validation and CORS
- **Agents**: LangGraph orchestrating 5 agents + aggregator (unchanged)

---

## 📁 Project Structure

```
MindMate/
├── backend/
│   ├── agents/              # Agent implementations (DO NOT MODIFY)
│   ├── graph/               # LangGraph flow (DO NOT MODIFY)
│   ├── api.py              # FastAPI integration layer
│   ├── main.py             # Original CLI runner
│   └── requirements.txt    # Python dependencies
│
└── frontend/
    ├── app/
    │   ├── page.jsx        # Main application page
    │   ├── layout.jsx      # Root layout
    │   └── globals.css     # Global styles
    ├── components/
    │   ├── WeightSlider.jsx    # Agent weight control
    │   ├── AgentCard.jsx       # Agent output display
    │   └── LoadingSpinner.jsx  # Loading animation
    ├── package.json
    ├── tailwind.config.js
    └── next.config.js
```

---

## 🚀 Setup Instructions

### Prerequisites

- **Python 3.9+** with pip
- **Node.js 18+** with npm
- Environment variables for LLM API keys (if used by agents)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Note: You may need to install additional dependencies for LangGraph and the agents. Check the agent files for specific requirements.

4. **Run the FastAPI server**:
   ```bash
   python api.py
   ```
   
   Server will start at: `http://localhost:8000`
   
   API docs available at: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```
   
   Frontend will start at: `http://localhost:3000`

---

## 🎮 Usage

1. **Start both servers** (backend on :8000, frontend on :3000)

2. **Open** `http://localhost:3000` in your browser

3. **Enter your decision query** in the large text area
   - Example: "Should I leave my current job to start a startup?"

4. **Adjust agent weights** using the sliders (0.0 to 1.0)
   - Default: All agents weighted equally at 0.2

5. **Click "Run MindMate"** to execute

6. **View results**:
   - **Council Resolution**: Final aggregated decision (prominent panel)
   - **Individual Perspectives**: Each agent's analysis (cards below)

---

## 🎨 Design Features

### Visual Style
- **Dark mode only** with neon accents (cyan, violet, emerald)
- **Glassmorphism** effects on all panels
- **Animated gradient background**
- **Neon glows** on interactive elements

### Animations (Framer Motion)
- Staggered card entrance animations
- Smooth loading spinner with pulsing effects
- Hover interactions on buttons and sliders
- Scale animations on value changes

### Responsive Design
- Mobile-first approach
- Grid layouts adapt to screen size
- Touch-friendly controls

---

## 🔌 API Reference

### `POST /decision`

Execute the MindMate decision process.

**Request Body**:
```json
{
  "query": "Your decision question here",
  "weights": {
    "ethical": 0.2,
    "risk": 0.2,
    "eq": 0.2,
    "values": 0.2,
    "red_team": 0.2
  }
}
```

**Response**:
```json
{
  "agent_outputs": {
    "ethical": "Ethical agent's perspective...",
    "risk": "Risk agent's analysis...",
    "eq": "EQ agent's insights...",
    "values": "Values agent's view...",
    "red_team": "Red team's critique..."
  },
  "final_decision": "Aggregated council resolution..."
}
```

**Other Endpoints**:
- `GET /` - API info
- `GET /health` - Health check

---

## 🛠️ Development

### Backend Development

The backend is a **thin integration layer**. The agent logic and LangGraph flow are in separate files and should not be modified.

To add features:
- Modify `api.py` only
- Keep graph execution as a black box
- Add validation or middleware as needed

### Frontend Development

```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run start    # Production server
npm run lint     # ESLint
```

**Key Components**:
- `page.jsx` - Main app logic and layout
- `WeightSlider.jsx` - Reusable slider with animations
- `AgentCard.jsx` - Agent output card with staggered animations
- `LoadingSpinner.jsx` - Animated loading state

**Styling**:
- Tailwind utility classes
- Custom utilities in `globals.css`
- Framer Motion for animations

---

## 🐛 Troubleshooting

### Backend Issues

**Port already in use**:
```bash
# Change port in api.py, line 140:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**CORS errors**:
- Check that frontend URL is in `allow_origins` (api.py, line 33)
- Default: `http://localhost:3000`

**Graph initialization fails**:
- Ensure all agent dependencies are installed
- Check LLM API keys are set in environment

### Frontend Issues

**Module not found errors**:
```bash
rm -rf node_modules package-lock.json
npm install
```

**API connection fails**:
- Verify backend is running on port 8000
- Check `API_URL` in `app/page.jsx` (line 9)

**Build errors**:
- Ensure Node.js version is 18 or higher
- Clear Next.js cache: `rm -rf .next`

---

## 📦 Production Deployment

### Backend

1. Set environment variables for production
2. Use a production ASGI server (uvicorn with workers)
3. Configure proper CORS origins
4. Add authentication if needed

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
npm run build
npm run start
```

Or deploy to Vercel/Netlify (configure API_URL as environment variable).

---

## 📄 License

This project integrates existing LangGraph agents with a new FastAPI backend and Next.js frontend.

---

## 🙏 Credits

- **LangGraph** for multi-agent orchestration
- **FastAPI** for the backend API layer
- **Next.js** for the React framework
- **Framer Motion** for animations
- **Tailwind CSS** for styling

---

**Built with ⚡ for clarity in decision-making**
