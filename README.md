# 🎮 Metacritic Web Scraper (Django + RAWG)

A robust, database-backed Python scraper that collects video game data from [Metacritic](https://www.metacritic.com) and enriches it with game images via the [RAWG API](https://rawg.io/apidocs). Built to integrate with Django ORM and handle image compression automatically.

---

## 📌 Features

- Scrapes games from **Metacritic** (title, scores, summary, platform, release date, etc.)
- Fetches game cover images via the **RAWG API**
- Compresses large images (>1MB) before saving
- Uses **Django ORM** for database integration
- Includes **resume functionality** using a `Page` model
- Logs scraping activity to `scraper.log`
- Built-in retry and rate-limit mechanisms

---

## 🧱 Requirements

- Python 3.9+
- Django 3.2+
- PostgreSQL or SQLite (via Django settings)
- RAWG API Key (free to obtain from [RAWG.io](https://rawg.io/apidocs))
- `Pillow`, `python-dotenv`, `beautifulsoup4`, etc.

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/RezaTaheri01/metacritic-web-scraper.git
cd metacritic-web-scraper
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd scraper
pip install -r req.txt
```

---

## 🌱 Django Integration

### 3. Apply Migrations

```bash
python manage.py makemigrations games
python manage.py migrate
```

### 4. Create Super User
```bash
python manage.py createsuperuser
```

---

## 🔐 RAWG API Key Setup

Create a `.env` file at the root of the project:

```
RAWG_API_KEY=your_rawg_api_key_here
```

You can register for a free RAWG API key here: https://rawg.io/apidocs

---

## 🚀 Running the Scraper

You can toggle between fetching full data or just completing images:

* Scrape metadata (no images)
    ```python
    python scraper.py
    ```

* Download images only
    ```python
    python scraper.py --images
    ```

* Full scrape (metadata + images)
    ```python
    python scraper.py --all
    ```

* Recheck mode
    ```python
    python scraper.py --recheck
    ```

    This mode reprocesses games from games.txt. It fetches each game again, checks for missing data, and logs any failures.

---

## 🗂️ Logs

Scraping activity and errors are logged to:

```
scraper.log
```

---

## 🛠️ Notes

- The script obeys a 30-second crawl delay between each game to avoid rate-limiting.
- If interrupted, scraping will resume from the last saved page (`Page` model).
- Images larger than 1MB are compressed to JPEG before saving.

---

## 🤝 Contributing

Pull requests and issue reports are welcome! If you want to contribute improvements (e.g., support for reviews, genres, or more APIs), feel free to fork and send a PR.

---

## ⚠️ Disclaimer:  
This project is for educational and non-commercial hobby use only.  
It is not affiliated with or endorsed by Metacritic.  
Please respect the Terms of Service of any site you interact with.

