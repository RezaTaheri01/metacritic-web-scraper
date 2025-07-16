# TODO: async get_games_images (Multiprocessing) Done

import os
import time
import random
import logging
import requests
import argparse
from datetime import datetime

from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

from concurrent.futures import ThreadPoolExecutor

load_dotenv()  # This loads variables from .env into os.environ


# region Django
import django
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper.settings')
django.setup()

from games.models import Game, Page
# endregion


# region Variables
api_key = os.getenv("RAWG_API_KEY")
max_size_bytes = 1 * 1024 * 512  # 0.5MB

base_url = "https://www.metacritic.com"
base_image_url = 'https://api.rawg.io/api/games?key={}&search="{}"&page_size={}'
games_url = "https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

retry_delay = 16
crawl_delay = 6
delay_plus = 4

last_page = 574
max_retries = 1_000
fetch_images = True

# Global thread executor (reuse across calls)
executor = None
max_workers = 2

current_line = 0
# endregion


# Configure basic logging to a file
logging.basicConfig(filename='scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)


# region Save
def save_failed_pages(pg):
    with open("failed_pages.txt", "a") as f:
        f.write(f"{pg}\n")


def save_failed_slugs(slug):
    with open("failed_slugs.txt", "a") as f:
        f.write(f"{slug}\n")
    

def save_games(gs):
    with open("games.txt", "a") as f:
        for g in gs:
            f.write(f"{g}\n")
# endregion


def main():
    pg = Page.objects.all().first()
    if not pg:
        # Create new Page model start from 1
        pg = Page()
        pg.save()
    current_page = pg.page_number

    for page in range(current_page, last_page + 1):
        print(f"Page {page} started.")

        games = get_games_page_html(games_url.format(page))
        
        if games:
            random.shuffle(games)
            if len(games) != 24:
                save_failed_pages(page)
                logger.warning(f"Page {page} does not include 24 urls! Found: {len(games)}")

            print(games)
            for g in games:
                print(f"Fetching {g}...")
                
                if g[-1] != "/":
                    g += "/"
                slug = g.split("/")[-2]
                
                response = get_game(base_url + g, slug)
                if response == None:
                    save_failed_slugs(slug)
                    logger.warning(f"{slug} return None")     
        else:
            save_failed_pages(page)
            logger.warning(f"Page {page} not fetched")
            
        print(f"Page {page} fetched")
        save_games(games)
        pg.page_number = page + 1
        pg.save()


def recheck():
    global current_line
    if os.path.exists("games.txt"):
        games_list = []
        with open("games.txt", "r") as f:
            games_list = f.readlines()[current_line:]
            
        print(f"Duplicates: {len(games_list) - len(set(games_list))}")
        for g in set(games_list):
            g = g[:-1]
                
            if g[-1] != "/":
                g += "/"
            slug = g.split("/")[-2]
            
            response = get_game(base_url + g, slug)
            if response == True:
                print(f"{g} Fetched")
            elif response == None:
                save_failed_slugs(slug)
                logger.warning(f"get_game on {slug} return None")

                
            current_line += 1


# List of games on each page
def get_games_page_html(url):
    time.sleep(random.uniform(crawl_delay, crawl_delay + delay_plus))
    
    games_links = []
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        game_links = soup.find_all(
            "a", class_="c-finderProductCard_container")

        for link in game_links:
            games_links.append(link['href'])
    else:
        logger.error(f"Failed to fetch games list. Status code: {response.status_code}")

    return games_links


# region Images
def get_game_image(title: str, slug: str):
    def fetch_image(query):
        url = base_image_url.format(api_key, query, 1)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0].get("background_image")
        return None

    image_url = fetch_image(title) or fetch_image(slug.replace("-", " ")) or fetch_image(slug)
    try:
        current_game = Game.objects.get(slug=slug)
    except:
        return

    if image_url:
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            original_size = len(img_response.content)
            # logger.info(f"📦{title} Original image size: {original_size / 1024:.2f} KB")

            if original_size > max_size_bytes:
                try:
                    # Open image with Pillow
                    img = Image.open(BytesIO(img_response.content))
                    
                    # Resize (optional): reduce dimensions (e.g. max width = 800)
                    max_width = 1920
                    if img.width > max_width:
                        height = int((max_width / img.width) * img.height)
                        img = img.resize((max_width, height), Image.Resampling.LANCZOS)

                    # Compress and save to buffer
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=70)
                    buffer.seek(0)
                    # logger.info("📉 Image compressed because it was larger than max_size_bytes")
                    current_game.image.save(f"{slug}.jpg", ContentFile(buffer.read()), save=True)
                    current_game.save()
                except Exception as e:
                    logger.error(f"❌ {slug} Error compressing image: {e}")
            else:
                # Image is small enough, save as-is
                current_game.image.save(f"{slug}.jpg", ContentFile(img_response.content), save=True)
                current_game.save()
                # logger.info("✅ Image saved without compression (already under max_size_bytes)")
        else:
            logger.error(f"❌ {title} Failed to download image from {image_url}")
    else:
        current_game.image_failed = True
        current_game.save()
        logger.error(f"❌ {title} No image found for '{title}' or '{slug}'")


def complete_games_images():
    games_no_img = Game.objects.filter(image="", image_failed=False)
    
    if not games_no_img.exists():
        return True  # All images already set
    
    for game_no_img in games_no_img:
        try:
            print(f"Fetching image for {game_no_img.slug}")
            get_game_image(game_no_img.title, game_no_img.slug)
        except Exception as e:
            logger.warning(f"Failed to fetch/save image for {game_no_img.slug}: {e}")
    
    # Recheck if all games now have images
    return not Game.objects.filter(image="", image_failed=False).exists()
# endregion


# region Get Single Game
def get_game_detail(url, slug, game: Game) -> bool:
    """
    Return True if data is extracted and assigned to the Game instance.
    Actual saving should be done outside this function.
    """
    time.sleep(random.uniform(crawl_delay, crawl_delay + delay_plus))

    try:
        response = requests.get(url + "details/", headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"{url} - Request failed: {e}")
        return False

    if response.status_code != 200:
        logger.error(
            f"{url} - Failed to fetch details. Status code: {response.status_code}")
        return False

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract Summary
        summary_div = soup.find(
            "div", class_="c-pageProductDetails_description")
        summary = summary_div.text.strip() if summary_div else "No description available."
        summary = summary.replace("Description:", "").strip()

        # Extract Platforms
        platform_names = []
        platforms_div = soup.find('div', class_="c-gameDetails_Platforms")
        if platforms_div:
            platform_tags = platforms_div.find_all(
                'li', class_='c-gameDetails_listItem')
            platform_names = [p.text.strip() for p in platform_tags]

        # Extract release date
        release_date_str = ""
        release_span = soup.find(
            'span', class_='g-outer-spacing-left-medium-fluid')
        if release_span:
            release_date_str = release_span.text.strip()
            try:
                release_date = datetime.strptime(
                    release_date_str, '%b %d, %Y').date()
            except ValueError:
                release_date = None
                logger.warning(
                    f"{url} - Failed to parse release date: {release_date_str}")
        else:
            release_date = None

        # Extract Developer
        developer = "Unknown"
        developer_div = soup.find('div', class_="c-gameDetails_Developer")
        if developer_div:
            dev_tag = developer_div.find(
                'a') or developer_div.find_all('span')[-1]
            if dev_tag:
                developer = dev_tag.text.strip()

        # Extract Publisher
        publisher = "Unknown"
        publisher_div = soup.find('div', class_="c-gameDetails_Distributor")
        if publisher_div:
            pub_tag = publisher_div.find(
                'a') or publisher_div.find_all('span')[-1]
            if pub_tag:
                publisher = pub_tag.text.strip()

        # Assign to Game instance
        game.release_date = release_date
        game.platforms = ", ".join(platform_names)
        game.developer = developer
        game.publisher = publisher
        game.summary = summary

        return True
    except Exception as e:
        logger.error(f"{url} - Error parsing details: {e}")
        return False


def get_game(url, slug):
    # Search for duplicate & Create a new instance
    game: Game = Game.objects.filter(slug=slug).first()
    if game:
        return False
    time.sleep(random.uniform(crawl_delay, crawl_delay + delay_plus))
    game = Game()

    # Get title and scores
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"{url} - Request failed: {e}")
        return None
    
    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.text, "html.parser")

            title_div = soup.find("div", attrs={"data-testid": "hero-title"})
            title = title_div.text.strip() if title_div else "Unknown Title"

            meta_score_block = soup.find("div", attrs={"data-testid": "critic-score-info"})
            meta_score = (
                meta_score_block.find("div", class_="c-siteReviewScore").text.strip()
                if meta_score_block and meta_score_block.find("div", class_="c-siteReviewScore")
                else None
            )

            meta_score_count_block = soup.find("a", attrs={"data-testid": "critic-path"})
            meta_score_count = (
                meta_score_count_block.find("span").text.split()[2]
                if meta_score_count_block and meta_score_count_block.find("span")
                else None
            )

            user_score_block = soup.find("div", attrs={"data-testid": "user-score-info"})
            user_score = (
                user_score_block.find("div", class_="c-siteReviewScore").text.strip()
                if user_score_block and user_score_block.find("div", class_="c-siteReviewScore")
                else None
            )

            user_score_count_block = soup.find("a", attrs={"data-testid": "user-path"})
            user_score_count = (
                user_score_count_block.find("span").text.split()[2]
                if user_score_count_block and user_score_count_block.find("span")
                else None
            )

        except Exception as e:
            logger.error(f"{slug}\n{e}")
            return None
    else:
        save_failed_slugs(slug)
        logger.error(
            f"Failed to fetch data. Status code: {response.status_code}")
        return None

    if not get_game_detail(url, slug, game):
        return None

    try:
        game.title = title
        game.link = url
        game.slug = slug
        game.meta_score = meta_score
        game.meta_score_count = meta_score_count
        game.user_score = user_score
        game.user_score_count = user_score_count
        game.save()
    except Exception as e:
        logger.error(f"❌ Failed to save game {slug}: {e}")
        return None
    
    if fetch_images and not game.image and not game.image_failed:
        executor.submit(get_game_image, title, slug)
        
    return True
# endregion


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scraper tasks.")
    parser.add_argument(
        "--images",
        action="store_true",
        help="Run image completion task instead of main()"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run main() with get_game_image"
    )
    parser.add_argument(
        "--recheck",
        action="store_true",
        help="recheck from games.txt"
    )
    args = parser.parse_args()
    
    retries = 0
    while retries < max_retries:
        try:
            if args.images:
                if complete_games_images():
                    break
            elif args.all:
                executor = ThreadPoolExecutor(max_workers=max_workers)  # You can adjust the worker count
                main()
                break
            elif args.recheck:
                fetch_images = False
                recheck()
                break
            else: # Without images
                fetch_images = False
                main()
                break
        except Exception as e:
            logger.error(f"Error in main(): {e}")
            retries += 1

            if retries < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds... ({retries}/{max_retries})")
                time.sleep(random.uniform(retry_delay, retry_delay + delay_plus))
            else:
                logger.critical("Max retries exceeded. Exiting.")
        finally:
            if executor:
                executor.shutdown(wait=True)
