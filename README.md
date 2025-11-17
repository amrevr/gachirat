<div align="center">

# Gachirat - AI Tomogachi

### *Your CRT-Style Digital Pet & Health Companion*

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*A retro CRT-inspired digital pet powered by Gemini AI, computer vision, and real-time ESP32 hardware integration.*

[Features](#-features) • [Architecture](#️-architecture) • [Setup](#-quick-start) • [Database](#-database-schema) • [Tech Stack](#-tech-stack)

</div>

---

## Overview

**Gachirat** is an AI-powered digital pet that combines:
- **Food Classification**: Upload food images → ResNet50 + Gemini vision → health scoring
- **Contextual AI Chat**: Gemini LLM with RAG (Retrieval-Augmented Generation) for personalized conversations
- **Health Gamification**: Dynamic health system (0-20) with mood-driven animations
- **Hardware Integration**: Real-time ESP32 UDP communication for physical emotion display
- **Retro Aesthetic**: CRT-style UI with scanlines, glow effects, and pixel-perfect animations

---

## Key Features

### AI & Machine Learning
- **Gemini 2.5 Flash LLM** for natural language understanding
- **ResNet50 Computer Vision** for food classification 
    - **Gemini Vision Fallback** when confidence < 0.6
- **RAG System** with conversation history (food/finance/general contexts)
- **Health Scoring Algorithm** with category-based nutrition mapping

### Interactive Experience
- **CRT Retro UI** with animated GIFs (happy/sad/idle states)
- **Dynamic Health Bar** (0-20 range) with visual transitions
- **Mood System**: Health-based emotion changes (happy >10, sad ≤10)
- **Temporary Boosts**: Eating healthy food when sad triggers brief happiness
- **Special Users**: `dead_user` preset for testing (always 0 health)

###  Technical Infrastructure
- **Dockerized Deployment** with Docker Compose
- **PostgreSQL Database** with SQLAlchemy ORM 
- **ESP32 UDP Integration** (5-second heartbeat, emotion codes 0-4)
- **RESTful API** with Flask backend
- **Image Upload & Processing** with multi-stage classification pipeline

---

## Development Progress

### Feature Completion: **87%** Complete

```
████████████████████░░░ 13/15 features
```

| Feature Category | Feature | Status |
|-----------------|---------|--------|
| **Frontend** | CRT-style UI & animations | ✅ Complete |
| | Health bar & mood system | ✅ Complete |
| | Image upload interface | ✅ Complete |
| **Backend** | Gemini LLM integration | ✅ Complete |
| | Food classification (ResNet50) | ✅ Complete |
| | Gemini vision fallback | ✅ Complete |
| | RAG conversation system | ✅ Complete |
| **Database** | PostgreSQL ORM models | ✅ Complete |
| | Food/conversation logging | ✅ Complete |
| **Hardware** | ESP32 UDP integration | ✅ Complete |
| | 5-second heartbeat | ✅ Complete |
| **DevOps** | Docker Compose setup | ✅ Complete |
| **Finance** | Plaid API integration | ⬜ Missing |
| **Analytics** | Survival model (timeToDefault) | ⬜ Missing |

### Planned Features
- **Plaid Integration**: Bank account linking for financial advice based on real transaction data
- **Survival Model**: Time-to-default prediction for financial health scoring
- **Vector Search**: Semantic conversation search using pgvector embeddings

---

## System Architecture

### Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (CRT UI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ index.html   │  │  script.js   │  │    style.css         │  │
│  │ • Login      │  │ • State mgmt │  │ • CRT effects        │  │
│  │ • Chat UI    │  │ • ESP32 sync │  │ • Animations         │  │
│  │ • Upload     │  │ • Health bar │  │ • Scanlines/glow     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (Flask API)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ app.py - Main Flask Application                           │ │
│  │ • /api/login      → User auth & greeting generation       │ │
│  │ • /api/gemini     → LLM chat with RAG context             │ │
│  │ • /api/feed       → Food classification & health update   │ │
│  │ • /api/esp32      → UDP emotion state transmission        │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ food_classifier  │  │       database.py (ORM)              │ │
│  │ • ResNet50       │  │ • User, Conversation, FoodLog        │ │
│  │ • Gemini fallback│  │ • PlaidAccount (ready for future)    │ │
│  │ • Nutrition map  │  │ • Vector embeddings support          │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└──────────────────┬────────────────────────┬────────────────────┘
                   │                        │
         ┌─────────▼──────────┐   ┌─────────▼──────────┐
         │   PostgreSQL 15    │   │  ESP32 (UDP:5005)  │
         │ ┌────────────────┐ │   │ ┌────────────────┐ │
         │ │ users          │ │   │ │ Emotion display│ │
         │ │ conversations  │ │   │ │ • SAD (0)      │ │
         │ │ food_logs      │ │   │ │ • NEUTRAL (2)  │ │
         │ │ plaid_accounts │ │   │ │ • HAPPY (4)    │ │
         │ │ (pgvector ext) │ │   │ │ 5s heartbeat   │ │
         │ └────────────────┘ │   │ └────────────────┘ │
         └────────────────────┘   └────────────────────┘
```

### Component Breakdown

#### Frontend (`frontend/`)
- **index.html**: HTML structure with CRT container, health bar, chat interface
- **script.js**: 
  - State machine with transition table (idle/happy/sad)
  - ESP32 heartbeat (5-second interval)
  - Image upload handling
  - Chat history management
- **style.css**: Retro CRT effects (scanlines, glow, phosphor color)
- **tomo/**: Animated GIF assets (1-happy, 2-sad, 3-idle, 31/32-transitions)

#### Backend (`backend/`)
- **app.py**:
  - Flask routes with session management
  - Gemini LLM integration (2.5 Flash)
  - RAG conversation retrieval (context-aware responses)
  - Health calculation algorithm
  - ESP32 UDP communication
- **food_classifier.py**:
  - ResNet50 model (custom trained weights)
  - ImageNet label mapping
  - Gemini vision fallback (< 0.6 confidence)
  - Nutrition scoring (1-5 scale)
- **database.py**:
  - SQLAlchemy ORM models
  - Connection pooling
  - Database initialization

#### Hardware (`esp32/hackrpi2025_fw/`)
- C firmware for ESP32
- UDP listener on port 5005
- Emotion code mapping (0-4)
- Display driver integration

---

##  Database Schema

### PostgreSQL 15 + pgvector Extensions

The application uses **PostgreSQL** with support for vector embeddings (future semantic search).

#### Schema Overview

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    health INTEGER DEFAULT 20,  -- Health score (0-20)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table (RAG source)
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    conversation_state VARCHAR(50),  -- 'general_chat', 'food_discussion', 'financial_advice', etc.
    timestamp TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_state ON conversations(conversation_state);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);

-- Food logs table
CREATE TABLE food_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    food_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- 'fruit', 'vegetable', 'fast food', 'dessert', etc.
    health_score INTEGER,   -- 1-5 scale (1=unhealthy, 5=very healthy)
    confidence FLOAT,       -- Classification confidence (0.0-1.0)
    image_path VARCHAR(500),
    timestamp TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_food_logs_user_id ON food_logs(user_id);
CREATE INDEX idx_food_logs_timestamp ON food_logs(timestamp DESC);

-- Plaid accounts table (future feature)
CREATE TABLE plaid_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    access_token VARCHAR(500) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    account_name VARCHAR(255),
    account_type VARCHAR(100),  -- 'checking', 'savings', 'credit', etc.
    balance FLOAT,
    connected_at TIMESTAMP DEFAULT NOW(),
    last_synced TIMESTAMP
);
```

#### ORM Models (SQLAlchemy)

**`User`**
- Primary user account
- Health tracking (0-20 range)
- Relationships: `conversations`, `food_logs`, `plaid_accounts`

**`Conversation`**
- Chat history for RAG retrieval
- Filtered by `conversation_state` for context-specific responses
- States: `general_chat`, `food_discussion`, `food_image_request`, `financial_advice`, `food_log_lookup`

**`FoodLog`**
- Food classification results
- Nutrition scoring & categorization
- Image path storage (optional)

**`PlaidAccount`** *(planned)*
- Bank account connection metadata
- Access tokens & sync status
- Future: Real transaction analysis

#### RAG System

The database powers **Retrieval-Augmented Generation**:
1. **Query**: User sends message
2. **Retrieve**: Fetch last 5-10 relevant conversations by state
3. **Augment**: Inject context into Gemini prompt
4. **Generate**: LLM produces personalized response

Example query:
```python
conversations = db.query(Conversation).filter(
    Conversation.user_id == user_id,
    Conversation.conversation_state.in_(['food_discussion', 'food_image_request'])
).order_by(Conversation.timestamp.desc()).limit(5).all()
```

#### Future: Vector Embeddings
- Prepared for **pgvector** extension:
- Semantic search over conversation history
- Similar food query retrieval
- Clustering user behavior patterns

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- PostgreSQL 15+ (if running without Docker)
- ESP32 device (optional, for hardware integration)

### Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/amrevr/tomo.git
   cd tomo/tomogachi
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # - GEMINI_API_KEY (required)
   # - DATABASE_URL (auto-configured in Docker)
   ```

3. **Start services**
   ```bash
   docker-compose up --build
   ```

4. **Access the app**
   - Frontend: `http://localhost:80`
   - Backend API: `http://localhost:5000`

###  Manual Development Setup

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**
   ```bash
   # Create database
   createdb tomogachi_db
   
   # Set environment variable
   export DATABASE_URL="postgresql://user:password@localhost:5432/tomogachi_db"
   export GEMINI_API_KEY="your_gemini_api_key"
   ```

3. **Initialize database**
   ```bash
   python database.py
   ```

4. **Start backend**
   ```bash
   python app.py
   # Server runs on http://0.0.0.0:5000
   ```

5. **Open frontend**
   ```bash
   cd ../frontend
   # Open index.html in browser or use live server
   ```

###  ESP32 Configuration

Update `frontend/script.js` with your ESP32 IP:
```javascript
const ESP32_IP = '192.168.1.100';  // Your ESP32 IP
const ESP32_PORT = 5005;
```

Flash firmware from `esp32/hackrpi2025_fw/` using ESP-IDF or Arduino.

---

##  Usage Guide

###  Login
- Enter username (or create new account)
- Special user: `dead_user` (starts at 0 health for testing)

###  Chat with Gachirat
**General conversation:**
```
> Hi Gachirat!
> How are you?
```

**Food tracking:**
```
> I'm hungry
> I ate pizza
> [Upload food image]
```

**Financial advice:**
```
> How should I save money?
> Should I invest in stocks?
```

### Health System
- **Health Range**: 0-20
- **Mood Changes**:
  - Happy: Health > 10
  - Sad: Health ≤ 10
- **Food Impact**:
  - Healthy food (fruits/veggies): +4 to +5 health
  - Neutral food: 0 health change
  - Unhealthy food: -4 to -5 health
- **Special Behavior**: Eating healthy food when sad triggers temporary happy state (3 seconds)

###  ESP32 Integration
- Emotion codes sent via UDP every 5 seconds
- Codes: `SAD(0)`, `NEUTRAL(2)`, `HAPPY(4)`, transitions (1, 3)
- Hardware displays pet's mood in real-time

---

##  Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5/CSS3** | Structure & styling |
| **Vanilla JavaScript** | State management, API calls |
| **CRT Effects** | Scanlines, glow, phosphor styling |

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **Flask 3.0** | Web framework & REST API |
| **SQLAlchemy** | ORM for database operations |
| **Google Gemini 2.5 Flash** | LLM for chat & vision tasks |
| **PyTorch** | Deep learning framework |
| **ResNet50** | Food classification model |
| **Pillow (PIL)** | Image processing |

### Database
| Technology | Purpose |
|------------|---------|
| **PostgreSQL 15** | Primary database |
| **SQLAlchemy ORM** | Object-relational mapping |

### Hardware
| Technology | Purpose |
|------------|---------|
| **ESP32** | Microcontroller for emotion display |
| **UDP Protocol** | Real-time communication |
| **ESP-IDF/Arduino** | Firmware framework |

### DevOps
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration |
| **Nginx** | Reverse proxy & static files |

---

## Project Structure

```
tomogachi/
├── backend/
│   ├── app.py                    # Main Flask application (536 lines)
│   ├── food_classifier.py        # ResNet50 + Gemini vision (169 lines)
│   ├── database.py               # SQLAlchemy models (128 lines)
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend container config
│   ├── trained_weights           # ResNet50 model weights
│   └── classifier_test/          # Test images
│
├── frontend/
│   ├── index.html                # Main UI (304 lines)
│   ├── script.js                 # State machine & API client (492 lines)
│   ├── style.css                 # CRT styling
│   └── tomo/                     # Animated GIF assets
│       ├── 1-happy.gif
│       ├── 2-sad.gif
│       ├── 3-idle.gif
│       ├── 31-idle-to-happy.gif
│       └── 32-idle-to-sad.gif
│
├── esp32/
│   └── hackrpi2025_fw/           # ESP32 firmware (C)
│       ├── main/
│       │   ├── hackrpi2025_fw.c
│       │   ├── simple_wifi.c/h
│       │   ├── simple_spi.c/h
│       │   └── simple_animation_lib.c/h
│       └── CMakeLists.txt
│
├── docker-compose.yml            # Multi-container setup
├── nginx.conf                    # Nginx configuration
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## API Endpoints

### Authentication
```http
POST /api/login
Content-Type: application/json

{
  "username": "alice"
}

Response: {
  "success": true,
  "user_id": 123,
  "health": 15,
  "message": "Welcome back, alice!",
  "chat_greeting": "Hi alice! Great to see you! :3"
}
```

### Chat
```http
POST /api/gemini
Content-Type: application/json

{
  "input": "I'm hungry",
  "conversation_state": "initial",
  "username": "alice"
}

Response: {
  "response": "Ooh! What did you eat? Tell me! :3",
  "is_food_query": true,
  "conversation_state": "awaiting_description"
}
```

### Food Classification
```http
POST /api/feed
Content-Type: multipart/form-data

FormData:
  image: <file>
  username: "alice"

Response: {
  "response": "Wow, pizza! That's okay, but maybe add veggies next time! :)",
  "food_name": "pizza",
  "health_score": 2,
  "category": "fast food",
  "confidence": 0.87,
  "health": 13,
  "health_change": -4,
  "is_healthy_food": false,
  "hide_upload": true
}
```

### ESP32 Communication
```http
POST /api/esp32
Content-Type: application/json

{
  "emotion": 4,
  "ip": "192.168.1.100",
  "port": 5005
}

Response: {
  "success": true,
  "emotion": 4
}
```

---

## Testing

### Test Database Connection
```bash
cd backend
python database.py
# Output: [DEBUG] Connected to PostgreSQL successfully
```

### Test ESP32 Communication
```bash
# Send test UDP packet
echo -n '\x04' | nc -u <ESP32_IP> 5005
# Emotion code: 4 (HAPPY)
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Verify DATABASE_URL format
# postgresql://username:password@host:port/database
```

### Gemini API Errors
```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Check API quota
# Visit: https://aistudio.google.com/app/apikey
```

### ESP32 Not Responding
- Verify ESP32 is on same network
- Check firewall rules for UDP port 5005
- Update IP in `frontend/script.js`

---

## Acknowledgments

- **Google Gemini** for LLM, vision APIs and writing this README
- **PyTorch & torchvision** for ResNet50 implementation
- **CRT CSS effects** inspired by [CGoudouris CodePen](https://codepen.io/cgoudouris/pen/VKQBQR)
- **ImageNet** for transfer learning onto current architecture


<div align="center">

**Made by @EndangeredConfusion and @amrevr**

*Last updated: November 16, 2025*

</div>
