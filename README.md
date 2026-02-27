# 🔐 Secure AI Code Review System

An AI-powered full-stack web application that allows users to submit code snippets and receive intelligent feedback using LLM integration.

Built using Flask, SQLAlchemy, Bootstrap, and Gemini API.

---

## 🚀 Features

### 🔑 Authentication
- User Registration & Login
- Password hashing (Flask-Bcrypt)
- Secure session management
- Protected routes

### 📦 Snippet Management (Full CRUD)
- Add code snippets
- Edit snippets
- Delete snippets
- View snippet history
- User-based data isolation

### 🤖 AI Code Review
- LLM-powered code review (Gemini API)
- Intelligent prompt-based analysis
- Extracted rating system (e.g., 8.5/10)
- Review history tracking
- Graceful fallback if AI quota exceeded

### 📊 Analytics
- Average rating per snippet
- Rating badges on dashboard
- Search by title
- Filter by programming language

### 🎨 UI/UX
- Responsive Bootstrap interface
- Flash messages
- Confirmation prompts
- Clean dashboard layout

---

## 🛠 Tech Stack

| Layer        | Technology |
|--------------|------------|
| Backend      | Flask |
| Database     | SQLite + SQLAlchemy |
| Authentication | Flask-Login + Bcrypt |
| Forms        | Flask-WTF |
| Frontend     | HTML, Bootstrap |
| AI Integration | Gemini API |
| Version Control | Git + GitHub |

---