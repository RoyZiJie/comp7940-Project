# HKBU Buddy - Campus Assistant Chatbot

<div align="center">

![HKBU Buddy](https://img.shields.io/badge/HKBU-Buddy-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Docker](https://img.shields.io/badge/Docker-Container-blue)
![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20RDS-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**An intelligent HKBU campus assistant based on RAG technology, supporting course queries, professor information retrieval, campus facilities Q&A, and real-time web search**

[Try it on Telegram](https://t.me/HKBU_buddy_bot) | [Report Issue](https://github.com/RoyZiJie/comp7940-Project/issues)

</div>

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Technical Architecture](#technical-architecture)
- [Quick Start](#quick-start)
- [Deployment Architecture](#deployment-architecture)
- [Team Information](#team-information)

---

## 🎓 Project Overview

**HKBU Buddy** is an intelligent campus assistant Telegram bot designed specifically for Hong Kong Baptist University (HKBU). Built on RAG (Retrieval-Augmented Generation) technology with integrated web search capabilities, it retrieves information from 97+ course documents and professor profiles, while also fetching real-time information from the web, combining everything with the GPT-5 large language model to provide accurate, timely, and comprehensive campus information for HKBU students and faculty.

### Core Value

- 📚 **Course Information**: Quick access to course descriptions, credits, prerequisites
- 👨‍🏫 **Professor Information**: Research areas, contact information, office locations
- 🏫 **Campus Facilities**: Library hours, cafeteria locations, building information
- 📅 **Academic Calendar**: Important dates, exam schedules, registration deadlines
- 🌐 **Real-time Information**: Weather, news, and latest updates via web search

### Problem Statement

Students at HKBU often struggle to find accurate course information, professor details, and campus facility schedules due to scattered information sources. HKBU Buddy solves this by consolidating all information into a single, easy-to-use Telegram bot with AI-powered search capabilities and real-time web search.

---

## ✨ Features

### Core Features

| Feature | Description | Example Query |
|---------|-------------|---------------|
| **Course Query** | Search HKBU Computer Science courses | "What is COMP7430 about?" |
| **Professor Info** | Research areas and contact details | "Tell me about Professor CHEN Jie" |
| **Academic Calendar** | Important dates and deadlines | "When is the final exam?" |
| **Campus Facilities** | Library, cafeteria, building info | "When does the library open?" |
| **Conversation History** | Remembers previous questions | Follow-up questions supported |
| **Usage Statistics** | Track personal usage | "/stats" command |
| **Web Search** | Real-time information from the internet | "What's the weather in Hong Kong?" |

### Technical Features

- ✅ **RAG Technology**: Intelligent retrieval from 97+ PDF documents (1155 chunks)
- ✅ **Web Search Integration**: SerpAPI (Google Search) for real-time information
- ✅ **GPT-5 Integration**: Powered by HKBU GenAI Platform GPT-5 API
- ✅ **PostgreSQL Database**: Persistent chat history and session storage
- ✅ **Docker Containerization**: One-command deployment, consistent environment
- ✅ **CI/CD Automation**: GitHub Actions for automatic build and deployment
- ✅ **Cloud Hosting**: AWS EC2 + RDS high-availability architecture
- ✅ **Markdown Fallback**: Graceful handling of malformed markdown responses

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show welcome message |
| `/help` | Display help information and usage examples |
| `/clear` | Clear conversation history |
| `/stats` | View personal usage statistics |

---


## 🏗️ Technical Architecture

### Data Flow

1. User sends message via Telegram `@HKBU_buddy_bot`
2. RAG Engine performs **dual retrieval**:
   - Local keyword search across 97 HKBU PDF documents
   - Web search via SerpAPI (Google Search) for real-time information
3. Combined context is sent to **HKBU GenAI GPT-5 API**
4. GPT-5 generates natural language response
5. Response is logged to **AWS RDS PostgreSQL** (`chat_logs`, `user_sessions`)
6. Final answer is sent back to user via Telegram

### Technology Stack

| Category | Technology | Version | Description |
|----------|------------|---------|-------------|
| **Language** | Python | 3.11 | Primary development language |
| **Bot Framework** | python-telegram-bot | 22.7 | Telegram Bot API wrapper |
| **Local RAG** | PyPDF2 + Custom Keyword | 3.0+ | PDF parsing and local retrieval |
| **Web Search** | SerpAPI (Google Search) | - | Real-time web search integration |
| **LLM API** | HKBU GenAI Platform GPT-5 | - | Large language model interface |
| **Database** | PostgreSQL | 15 | Chat log and session storage |
| **Database Driver** | asyncpg | 0.29+ | Async PostgreSQL driver |
| **Container** | Docker | Latest | Application containerization |
| **CI/CD** | GitHub Actions | - | Automated build and deployment |
| **Cloud - Compute** | AWS EC2 | t3.micro | Bot runtime environment |
| **Cloud - Database** | AWS RDS | db.t4g.micro | Managed PostgreSQL |

---
## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Telegram account
- HKBU GenAI Platform API Key
- SerpAPI Key (optional, for web search)
- PostgreSQL (optional, for local database)

### Local Development Setup

#### 1. Clone the repository

```bash
git clone https://github.com/RoyZiJie/comp7940-Project.git
cd comp7940-Project

# Windows
python -m venv venv
source venv/Scripts/activate

# Mac/Linux
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Telegram Bot Token
TELEGRAM_TOKEN=your_telegram_bot_token_here

# HKBU GenAI Platform API Configuration
API_KEY=your_api_key_here
API_BASE_URL=https://genai.hkbu.edu.hk/api/v0/rest
MODEL=gpt-5
API_VERSION=2024-12-01-preview

# AWS RDS Database Configuration
DB_HOST=your_rds_endpoint_or_ip_here
DB_PORT=5432
DB_NAME=postgres
DB_USER=bot_user
DB_PASSWORD=your_database_password_here

# SerpAPI Web Search (optional)
SERPAPI_KEY=your_serpapi_key_here

# Run the bot
python bot.py

# Expected output:
✅ Loaded 97 documents → 1155 chunks
✅ Database connected
✅ Database tables ready
🤖 HKBU Buddy Telegram Bot started...
📱 Search for @HKBU_buddy_bot on Telegram to start using

comp7940-Project/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline
├── data/                       # Knowledge base (97 PDF files)
│   ├── COMP7015.pdf
│   ├── COMP7025.pdf
│   ├── ... (95 more PDFs)
│   └── msc_booklet.pdf
├── storage/                    # Vector index storage (auto-generated)
├── bot.py                      # Main Telegram bot application
├── rag_engine.py               # RAG engine with PDF processing + web search
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container configuration
├── .env                        # Environment variables (not committed)
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
```
## ☁️ Deployment Architecture

### Deploy with Docker (Local)

#### 1. Login to GitHub Container Registry

```bash
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_PERSONAL_ACCESS_TOKEN
```
#### 2. Pull the Docker image

```bash
docker pull ghcr.io/royzijie/comp7940-project:latest
```
#### 3. Run the container
```bash
docker run -d --name hkbu-buddy  --env-file .env ghcr.io/royzijie/comp7940-project:latest
```
#### 4. Verify the container is running
```bash
docker ps
docker logs hkbu-buddy
```
#### 5. Test the bot

Open Telegram and send a message to @HKBU_buddy_bot

### Deploy to AWS EC2 (Cloud)
This project is deployed on AWS EC2 for 24/7 cloud hosting.
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Pull and run
docker pull ghcr.io/royzijie/comp7940-project:latest
docker rm -f hkbu-buddy
docker run -d --name hkbu-buddy --restart unless-stopped --env-file .env ghcr.io/royzijie/comp7940-project:latest
docker logs hkbu-buddy
```

## 👥 Team Information

---

**Made with ❤️ by Group I - HKBU COMP7940 Team **

*Ye YaoZhang | Lan RuiPeng | Zhang ZiJie*

[🔝 Back to Top](#hkbu-buddy---campus-assistant-chatbot)






