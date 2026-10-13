# TalentIQ

AI-powered recruitment platform built with React, FastAPI,
LangChain, Groq Cloud, and PostgreSQL/pgvector.

## Overview

TalentIQ is a full-stack recruitment application designed
to help recruiters manage candidates, process CVs, and
search candidate profiles using artificial intelligence.

## Tech Stack

### Frontend
- React
- TypeScript
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic

### AI
- LangChain (planned)
- Groq Cloud API (planned)
- Sentence Transformers (planned)

### Database
- PostgreSQL 17
- pgvector

### DevOps
- Docker Compose
- GitHub Actions (planned)

## Features

- [ ] Candidate management
- [ ] PDF CV upload and parsing
- [ ] Semantic candidate search
- [ ] AI-powered candidate analysis
- [ ] Authentication and authorization
- [ ] Recruitment dashboard

## Getting Started

### Prerequisites

- Node.js 22+
- Python 3.12+
- Docker Desktop

### 1. Clone the repository

```bash
git clone https://github.com/YassYassId/TalentIQ.git
cd TalentIQ
```

### 2. Start PostgreSQL

Create a `.env` file from `.env.example` and configure
the database password.

```bash
docker compose up -d
```

### 3. Start the backend

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
```

Create `backend/.env` from `backend/.env.example` and
configure the database connection.

```bash
alembic upgrade head
fastapi dev app/main.py
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

## API Documentation

Once the backend is running:

http://127.0.0.1:8000/docs

## Project Status

Under active development.

## Disclaimer

The public demo will use synthetic candidate data.
AI-generated recommendations are intended to support
human recruiters, not automate hiring decisions.