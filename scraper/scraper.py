from datetime import datetime
from bs4 import BeautifulSoup
import requests
import logging
import time

# region Django
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper.settings')
django.setup()

from games.models import Game, Page
# endregion

base_url = "https://www.metacritic.com"
base_image_url = "https://www.igdb.com/games/"
games_url = "https://www.metacritic.com/browse/game/?releaseYearMin=1958&releaseYearMax=2025&page={}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}
crawl_delay = 60
last_page = 568
max_retries = 200

# Configure basic logging to a file
logging.basicConfig(filename='scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)


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
            print(games)
            for game in games:
                print(f"Fetching {game}...")
                if get_game(base_url + game) != False:
                    time.sleep(crawl_delay)

        print(f"Page {page} fetched.")

        pg.page_number = page + 1
        pg.save()


# List of games on each page
def get_games_page_html(url):
    games = []
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        game_links = soup.find_all(
            "a", class_="c-finderProductCard_container")

        for link in game_links:
            games.append(link['href'])
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

    return games


# Single Product details
def get_game_detail(url, game: Game) -> bool:
    """
    Return True if data is extracted and assigned to the Game instance.
    Actual saving should be done outside this function.
    """
    time.sleep(crawl_delay // 2)

    try:
        response = requests.get(url + "details/", headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"{url} - Request failed: {e}")
        return False

    if response.status_code != 200:
        logger.error(f"{url} - Failed to fetch details. Status code: {response.status_code}")
        return False

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract Summary
        summary_div = soup.find("div", class_="c-pageProductDetails_description")
        summary = summary_div.text.strip() if summary_div else "No description available."
        summary = summary.replace("Description:", "").strip()

        # Extract Platforms
        platform_names = []
        platforms_div = soup.find('div', class_="c-gameDetails_Platforms")
        if platforms_div:
            platform_tags = platforms_div.find_all('li', class_='c-gameDetails_listItem')
            platform_names = [p.text.strip() for p in platform_tags]

        # Extract release date
        release_date_str = ""
        release_span = soup.find('span', class_='g-outer-spacing-left-medium-fluid')
        if release_span:
            release_date_str = release_span.text.strip()
            try:
                release_date = datetime.strptime(release_date_str, '%b %d, %Y').date()
            except ValueError:
                release_date = None
                logger.warning(f"{url} - Failed to parse release date: {release_date_str}")
        else:
            release_date = None

        # Extract Developer
        developer = "Unknown"
        developer_div = soup.find('div', class_="c-gameDetails_Developer")
        if developer_div:
            dev_tag = developer_div.find('a') or developer_div.find_all('span')[-1]
            if dev_tag:
                developer = dev_tag.text.strip()

        # Extract Publisher
        publisher = "Unknown"
        publisher_div = soup.find('div', class_="c-gameDetails_Distributor")
        if publisher_div:
            pub_tag = publisher_div.find('a') or publisher_div.find_all('span')[-1]
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


def get_game(url):
    # Search for duplicate & Create a new instance
    slug = url.split("/")[-2]
    game: Game = Game.objects.filter(slug=slug).first()
    if game:
        return False
    game = Game()

    # Get title and scores
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.text, "html.parser")

            title_div = soup.find("div", attrs={"data-testid": "hero-title"})
            title = title_div.text.strip() if title_div else "Unknown Title"

            meta_score = soup.find(
                "div", attrs={"data-testid": "critic-score-info"})
            meta_score = meta_score.find("div", class_="c-siteReviewScore")

            meta_score_count = soup.find(
                "a", attrs={"data-testid": "critic-path"})
            meta_score_count = meta_score_count.find("span").text.split()[2]

            user_score = soup.find(
                "div", attrs={"data-testid": "user-score-info"})
            user_score = user_score.find("div", class_="c-siteReviewScore")

            user_score_count = soup.find(
                "a", attrs={"data-testid": "user-path"})
            user_score_count = user_score_count.find("span").text.split()[2]
        except Exception as e:
            logger.error(f"{slug}\n{e}")
            return
    else:
        logger.error(
            f"Failed to fetch data. Status code: {response.status_code}")
        return

    if not get_game_detail(url, game):
        return

    game.title = title
    game.link = url
    game.slug = slug
    game.meta_score = meta_score.text
    game.meta_score_count = meta_score_count
    game.user_score = user_score.text
    game.user_score_count = user_score_count
    game.save()
    return True


if __name__ == "__main__":
    retries = 0
    while retries < max_retries:
        try:
            main()
            break
        except Exception as e:
            logger.error(f"Error in main(): {e}")
            retries += 1
            if retries < max_retries:
                logger.info(f"Retrying in {crawl_delay} seconds... ({retries}/{max_retries})")
                time.sleep(crawl_delay)
            else:
                logger.critical("Max retries exceeded. Exiting.")
