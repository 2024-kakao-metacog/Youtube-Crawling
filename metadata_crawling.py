import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from xpath_repository import XPATHS


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

    # Current URL
    current_url = driver.current_url
    video_metadata["currentUrl"] = current_url

    # Crawl static data using bs4
    static_metadata = fetch_metadata_with_bs4(current_url, video_metadata)

    if not static_metadata:
        return None

    # 현재 영상이 광고 영상인지 확인
    # 광고 영상이 아닌 경우 예외 발생 -> 다음 메타데이터 수집
    try:
        ad_renderer = driver.find_element(By.XPATH, XPATHS["ad_renderer"].format(video_order=video_order))
        print(ad_renderer)
        if ad_renderer:
            return None
    
    except Exception as e:
        pass

    # Like Count
    like_button = driver.find_element(By.XPATH, XPATHS["like_button"].format(video_order=video_order))
    video_metadata["likeCount"] = like_button.text

    # Comment Count
    comment_count = driver.find_element(By.XPATH, XPATHS["comment_count"].format(video_order=video_order))
    video_metadata["commentCount"] = comment_count.text

    # Username
    username = driver.find_elements(By.XPATH, XPATHS["username"].format(video_order=video_order))

    if username:
        video_metadata["userName"] = username[0].text
    else:
        username = driver.find_element(By.XPATH, XPATHS["username"].format(video_order=video_order))
        video_metadata["userName"] = username.text

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
    driver.implicitly_wait(3)

    video_counter = 0
    for video_order in range(1, max_videos+1):
        video_metadata = {}

        try:
            video_metadata = fetch_dynamic_data_with_selenium(driver, video_metadata, video_order)

            # Click for Next Video
            WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, XPATHS["next_video_btn"].format(video_order=video_order))))
            next_video_btn = driver.find_element(By.XPATH, XPATHS["next_video_btn"].format(video_order=video_order))
            next_video_btn.click()

        # 예기치 않은 예외 발생 시
        # 다음 영상으로 넘어가기
        except Exception as e:
            # Click for Next Video
            WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, XPATHS["next_video_btn"].format(video_order=video_order))))
            next_video_btn = driver.find_element(By.XPATH, XPATHS["next_video_btn"].format(video_order=video_order))
            next_video_btn.click()
            continue

        # 테스트를 위한 메타데이터 출력
        # TODO: File writing
        print(video_order)
        if video_metadata:
            video_counter += 1
            print(video_counter)
            for key, value in video_metadata.items():
                print(f"{key}: {value}")
            print()
        else:
            print("데이터를 수집하지 못하였습니다.")
            print()


if __name__ == "__main__":
    # # Testing both functions
    video_url = "https://www.youtube.com/shorts/SB4Rc6aq9Dg"
    main(video_url)