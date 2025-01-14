import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from xpath_repository import XPATHS, SELECTORS

import csv


def save_metadata_in_csv(video_metadata, path="video_metadata.csv"):
    # CSV 파일 저장 경로
    csv_file_path = "video_metadata.csv"

    # CSV로 저장
    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=video_metadata.keys())
        writer.writerow(video_metadata)  # 데이터 작성


def fetch_metadata_with_bs4(video_url: str, video_metadata: dict) -> dict:
    """
    Fetch YouTube video metadata using BeautifulSoup.

    Parameters:
        video_url (str): The URL of the YouTube video.
        video_metadata (dict): Dictionary to store video metadata.

    Retrieves the following metadata:
        - Title: The title of the video from the "og:title" meta tag.
        - Description: The video's description from the "og:description" meta tag.
        - Thumbnail URL: The thumbnail image URL from the "og:image" meta tag.
        - Published Date: The published date from the "datePublished" meta tag.
        - View Count: The total views from the "interactionCount" meta tag.

    Returns:
        dict: Updated `video_metadata` dictionary with the fetched metadata.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(video_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch video data. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Title
    title = soup.find("meta", property="og:title")
    video_metadata["title"] = title["content"] if title else "N/A"

    # Description
    description = soup.find("meta", property="og:description")
    video_metadata["description"] = description["content"] if description else "N/A"

    # Thumbnail URL
    thumbnail = soup.find("meta", property="og:image")
    video_metadata["thumbnail"] = thumbnail["content"] if thumbnail else "N/A"

    # Published Date
    published_date = soup.find("meta", itemprop="datePublished")
    video_metadata["publishedAt"] = published_date["content"] if published_date else "N/A"

    # View Count
    view_count = soup.find("meta", itemprop="interactionCount")
    video_metadata["viewCount"] = view_count["content"] if view_count else "N/A"

    return video_metadata


def fetch_dynamic_data_with_selenium(driver: webdriver.Chrome, video_url: str, video_metadata: dict, video_order: int) -> dict:
    """
    Fetch YouTube Shorts video metadata dynamically using Selenium.

    Parameters:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        video_url (str): URL of the current YouTube Shorts video.
        video_metadata (dict): Dictionary to store video metadata.
        video_order (int): The position of the video in the YouTube Shorts reel.

    Retrieves the following metadata dynamically:
        - Like Count: Number of likes from the like button text.
        - Comment Count: Number of comments from the comment button text.
        - Username: The uploader's username from the channel metadata.
        - Current URL: URL of the currently playing video.

    Calls `fetch_metadata_with_bs4` to retrieve static metadata.

    Returns:
        dict: Updated `video_metadata` dictionary with the fetched metadata.
    """


    # 동적 요소 모두 로딩될 때까지 대기
    # 광고인 경우 Timeout
    meta_panel = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, XPATHS["meta_panel"].format(video_order=video_order))))
    action_panel = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, XPATHS["action_panel"].format(video_order=video_order))))

    # VideoURL
    video_url = driver.current_url
    video_metadata["currentUrl"] = video_url

    # Crawl static data using bs4
    static_metadata = fetch_metadata_with_bs4(video_url, video_metadata)

    if not static_metadata:
        return None

    # Like Count
    like_button = action_panel.find_element(By.CSS_SELECTOR, SELECTORS["like_button"])
    video_metadata["likeCount"] = like_button.text

    # Comment Count
    comment_count = action_panel.find_element(By.CSS_SELECTOR, SELECTORS["comment_count"])
    video_metadata["commentCount"] = comment_count.text

    # Username
    username = meta_panel.find_element(By.CSS_SELECTOR, SELECTORS["username"])
    video_metadata["username"] = username.text

    # Click for Next Video
    next_video_btn = driver.find_element(By.CSS_SELECTOR, SELECTORS["next_video_btn"])
    next_video_btn.click()

    return video_metadata


def initiate_driver():
    """
    Initialize a headless Selenium WebDriver for scraping.

    Configures the following options:
        - Headless mode for non-GUI execution.
        - Disables sandboxing for compatibility.
        - Sets window size for consistent rendering.

    Returns:
        webdriver.Chrome: The initialized WebDriver instance.
    """
    
    # Selenium Chrome options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=860,540")

    # Driver setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def main(url):
    """
    Main function to scrape metadata from YouTube Shorts videos.

    Parameters:
        url (str): The URL of the YouTube Shorts page to start scraping.

    Workflow:
        - Initializes a headless Selenium WebDriver.
        - Navigates to the provided YouTube Shorts URL.
        - Iterates through videos in the reel sequentially.
        - Calls `fetch_dynamic_data_with_selenium` to scrape each video's metadata.
        - Handles errors (e.g., ads) by skipping to the next video.
        - Saves scraped metadata to a CSV file.
    """

    # Driver start
    driver = initiate_driver()
    driver.get(url)

    video_order = 1
    while True:
        video_metadata = {}

        try:
            video_metadata = fetch_dynamic_data_with_selenium(driver, url, video_metadata, video_order)

        # 예기치 않은 예외 발생 시(ex. 광고 영상)
        # 다음 영상으로 넘어가기
        except Exception as e:
            # Click for Next Video
            next_video_btn = driver.find_element(By.CSS_SELECTOR, SELECTORS["next_video_btn"])
            next_video_btn.click()

            video_order += 1
            continue

        save_metadata_in_csv(video_metadata)

        video_order += 1

if __name__ == "__main__":
    # Start scraping from a given Shorts video URL
    video_url = "https://www.youtube.com/shorts/SB4Rc6aq9Dg"
    main(video_url)