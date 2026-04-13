# HKBU Buddy - Campus Assistant Chatbot

<div align="center">

![HKBU Buddy](https://img.shields.io/badge/HKBU-Buddy-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Docker](https://img.shields.io/badge/Docker-Container-blue)
![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20RDS-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**An intelligent HKBU campus assistant based on RAG technology, supporting course queries, professor information retrieval, campus facilities Q&A, and more**

[Try it on Telegram](https://t.me/HKBU_buddy_bot) | [Report Issue](https://github.com/RoyZiJie/comp7940-Project/issues)

</div>

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Technical Architecture](#technical-architecture)
- [Quick Start](#quick-start)
- [Team Information](#team-information)

---

## 🎓 Project Overview

**HKBU Buddy** is an intelligent campus assistant Telegram bot designed specifically for Hong Kong Baptist University (HKBU). Built on RAG (Retrieval-Augmented Generation) technology, it retrieves information from 97+ course documents and professor profiles, combining it with the GPT-5 large language model to provide accurate and timely campus information for HKBU students and faculty.

### Core Value

- 📚 **Course Information**: Quick access to course descriptions, credits, prerequisites
- 👨‍🏫 **Professor Information**: Research areas, contact information, office locations
- 🏫 **Campus Facilities**: Library hours, cafeteria locations, building information
- 📅 **Academic Calendar**: Important dates, exam schedules, registration deadlines

### Problem Statement

Students at HKBU often struggle to find accurate course information, professor details, and campus facility schedules due to scattered information sources. HKBU Buddy solves this by consolidating all information into a single, easy-to-use Telegram bot with AI-powered search capabilities.

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

### Technical Features

- ✅ **RAG Technology**: Intelligent retrieval from 97+ PDF documents (1155 chunks)
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

### Architecture Diagram

### Technology Stack

| Category | Technology | Version | Description |
|----------|------------|---------|-------------|
| **Language** | Python | 3.11 | Primary development language |
| **Bot Framework** | python-telegram-bot | 22.7 | Telegram Bot API wrapper |
| **RAG Engine** | PyPDF2 + Custom Keyword | 3.0+ | PDF parsing and intelligent retrieval |
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

# Environment Variables Configuration
Create a `.env` file in the project root directory with the following content:

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

# Run the bot
python bot.py

# Expected output:
✅ Loaded 97 documents → 1155 chunks
✅ Database connected
✅ Database tables ready
🤖 HKBU Buddy Telegram Bot started...
📱 Search for @HKBU_buddy_bot on Telegram to start using

📁 Project Structure
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
├── rag_engine.py               # RAG engine with PDF processing
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container configuration
├── docker-compose.yml          # Multi-container orchestration
├── .env                        # Environment variables (not committed)
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
└── LICENSE                     # MIT License

```
## 👥 Team Information

---

**Made with ❤️ by Group I - HKBU COMP7940 Team **

*Ye YaoZhang | Lan RuiPeng | Zhang ZiJie*

[🔝 Back to Top](#hkbu-buddy---campus-assistant-chatbot)






