import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

def fetch_dynamic_data_with_selenium(driver: webdriver.Chrome, video_metadata: dict, video_order: int) -> dict:
    """
    Fetch YouTube video metadata dynamically using Selenium.

    Parameters:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        video_metadata (dict): Dictionary to store video metadata.
        video_order (int): The position of the video in the YouTube Shorts reel.

    Retrieves the following metadata dynamically:
        - Like Count: Number of likes using the like button's text.
        - Comment Count: Number of comments using the comment button's text.
        - Username: The uploader's username, using multiple fallback methods.
        - Current URL: The URL of the currently playing video.

    Additionally, calls `fetch_metadata_with_bs4` to retrieve static metadata.

    Returns:
        dict: Updated `video_metadata` dictionary with the fetched metadata.
    """

    # Wait until Username is rendered
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[3]/div[2]/ytd-reel-video-renderer[{video_order}]/div[4]/ytd-reel-player-overlay-renderer/div[1]/div[1]/div/yt-reel-metapanel-view-model')))

    # Like Count
    like_button = driver.find_element(By.XPATH, f"/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[3]/div[2]/ytd-reel-video-renderer[{video_order}]/div[4]/ytd-reel-player-overlay-renderer/div[2]/div/div[1]/ytd-like-button-renderer/ytd-toggle-button-renderer[1]/yt-button-shape/label/div/span")
    video_metadata["likeCount"] = like_button.text

    # Comment Count
    comment_count = driver.find_element(By.XPATH, f"/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[3]/div[2]/ytd-reel-video-renderer[{video_order}]/div[4]/ytd-reel-player-overlay-renderer/div[2]/div/div[2]/ytd-button-renderer/yt-button-shape/label/div/span")
    video_metadata["commentCount"] = comment_count.text

    # Username
    username = driver.find_elements(By.XPATH, f"/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[3]/div[2]/ytd-reel-video-renderer[{video_order}]/div[4]/ytd-reel-player-overlay-renderer/div[1]/div[1]/div/yt-reel-metapanel-view-model/div[1]/yt-reel-channel-bar-view-model/span/a")

    if username:
        video_metadata["userName"] = username[0].text
    else:
        username = driver.find_element(By.XPATH, f"/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[3]/div[2]/ytd-reel-video-renderer[{video_order}]/div[4]/ytd-reel-player-overlay-renderer/div[1]/div[1]/div/yt-reel-metapanel-view-model/div[2]/yt-reel-channel-bar-view-model/span/a")
        video_metadata["userName"] = username.text

    # Current URL
    current_url = driver.current_url
    video_metadata["currentUrl"] = current_url

    # Crawl static data using bs4
    fetch_metadata_with_bs4(current_url, video_metadata)

    return video_metadata

def main(url, max_videos=10000):
    """
    Main function to scrape metadata from YouTube Shorts videos.

    Parameters:
        url (str): The URL of the YouTube Shorts page to start scraping.
        max_videos (int): Maximum number of videos to process (default is 10,000).

    Workflow:
        - Initializes a headless Selenium WebDriver.
        - Navigates to the provided YouTube Shorts URL.
        - Iterates through videos in the reel up to `max_videos`.
        - Calls `fetch_dynamic_data_with_selenium` to scrape each video's metadata.
        - Handles errors (e.g., ads) by skipping to the next video.
        - Stores scraped metadata in `video_metadata_list`.

    Prints:
        - Video order and its metadata for each processed video.
    """

    video_metadata_list = []

    # Selenium Chrome options
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=860,540")

    # Driver setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Driver start
    driver.get(url)

    for video_order in range(1, max_videos+1):
        video_metadata = {}

        try:
            fetch_dynamic_data_with_selenium(driver, video_metadata, video_order)

            # Click for Next Video
            next_video_btn = driver.find_element(By.XPATH, "/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[5]/div[2]/ytd-button-renderer/yt-button-shape/button")
            next_video_btn.click()

        # 광고 영상인 경우(건너뛰기)
        except Exception as e:
            # Click for Next Video
            next_video_btn = driver.find_element(By.XPATH, "/html/body/ytd-app/div[1]/ytd-page-manager/ytd-shorts/div[5]/div[2]/ytd-button-renderer/yt-button-shape/button")
            next_video_btn.click()

            continue

        video_metadata_list.append(video_metadata)

        # 테스트를 위한 메타데이터 출력
        print(video_order)
        for key, value in video_metadata.items():
            print(f"{key}: {value}")
        print()


if __name__ == "__main__":
    # # Testing both functions
    video_url = "https://www.youtube.com/shorts/SB4Rc6aq9Dg"
    main(video_url)