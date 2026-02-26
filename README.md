# Pokémon Tracker

A Python + Flask application to manage, search, and track Pokémon card collections with live pricing updates.

<img width="800" height="600" alt="image" src="https://github.com/user-attachments/assets/926f2d2c-e32d-429b-8368-7fc7f5bed22d" />


![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)

## ✨ Features

* **Browse Cards** - View all cards in your collection via web interface
* **Add Cards** - Search and add cards by name, set, and rarity
* **Remove Cards** - Delete cards from your collection
* **Price Refresh** - Automatically update all card prices from tcgcsv
* **Real-time Pricing** - Live market prices via Pokémon tcgcsv
* **Collection Stats** - View total cards, collection value, and average value

## 🛠️ Tech Stack

* **Backend**: Python, Flask
* **Database**: PostgreSQL
* **APIs**: Pokémon TCG API (pokemontcg.io)
* **Frontend**: HTML, CSS, Vanilla JavaScript
* **Libraries**: `psycopg2`, `requests`, `flask_cors`, `gunicorn`

## 🚀 Installation

1. **Clone and setup:**

```bash
git clone 
cd pokemon-tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Create PostgreSQL database:**

```sql
CREATE DATABASE pokemon_tracker;
```

3. **Set environment variables:**

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/pokemon_tracker"
# Optional: export POKEMON_TCG_API_KEY="your-api-key"
```

4. **Run the app:**

```bash
python app.py
```

Visit: `http://localhost:5000`

## 🔌 API Endpoints

### Card Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cards` | Get user's cards |
| POST | `/api/add-card` | Add card (`name`, `set_name`, `rarity`) |
| POST | `/api/remove-card` | Remove card (`name`) |
| POST | `/api/refresh-prices` | Update all prices |

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | No | Flask session secret (auto-generates if not set) |
| `POKEMON_TCG_API_KEY` | No | API key for 20k/day limit (vs 1k/day free) |

**For local development only:**

| Variable | Description |
|----------|-------------|
| `DB_NAME` | Database name (if not using DATABASE_URL) |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `DB_HOST` | Database host (default: localhost) |
| `DB_PORT` | Database port (default: 5432) |

## 📝 Usage Examples

**Add a card:**
```bash
POST /api/add-card
{
  "name": "Pikachu",
  "set_name": "151",
  "rarity": "Common"
}
```

**Remove a card:**
```bash
POST /api/remove-card
{
  "name": "Pikachu"
}
```

**Refresh prices:**
```bash
POST /api/refresh-prices
```
