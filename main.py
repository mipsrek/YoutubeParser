from os import waitpid
from tokenize import String
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import networkx as nx
from selenium.webdriver.ie.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

INITIAL_URL = "https://www.youtube.com/watch?v=CpCKkWMbmXU"
DEPTH = 3
NUMBER_RECOMMENDATIONS = 3
KEY_WORDS = ["israel", "deep state", "climate change"]
NUMBER_SEARCH = 1

# avoid repeating webdriver waits
def wait_for(driver, condition, timeout=60):
    return WebDriverWait(driver, timeout).until(condition)


def accept_cookies(driver):
    driver.find_element(By.XPATH, "//*[@id=\"content\"]/div[2]/div[6]/div[1]/ytd-button-renderer[2]/yt-button-shape/button").click()
    print("Accepted cookies")


def get_video_title(driver):
    video_title = wait_for(driver, EC.presence_of_element_located((By.ID, "title")))
    return video_title.text

    # try:
    #     video_title = (driver
    #                    .find_element(By.ID, "title")
    #                    .find_element(By.TAG_NAME, "yt-formatted-string").text)
    # except:
    #     video_title = "**Empty**"
    # return video_title

# # TODO get comments under video
# def get_comments(driver):
#     driver.execute_script("window.scrollTo(0, 600);")
#     time.sleep(3)
#     comments = driver.find_element(By.ID, "comments").find_elements(By.ID, "contents")


def get_channel(driver):
    channel = wait_for(driver, EC.presence_of_element_located((By.XPATH, "//*[@id=\"text\"]/a")))
    return channel.text


# TODO change to the actual number?
# This is returning the text value of the button, not the actual number of likes
def get_likes(driver):
    likes_xpath = "//*[@id=\"top-level-buttons-computed\"]/segmented-like-dislike-button-view-model/yt-smartimation/div/div/like-button-view-model/toggle-button-view-model/button-view-model/button/div[2]"
    if driver.find_elements(By.XPATH, likes_xpath):
        return driver.find_element(By.XPATH, likes_xpath).text
    else:
        return "Emtpy"


def get_description(driver):
    if driver.find_elements(By.ID, "expand"):
        driver.find_element(By.ID, "expand").click()
        if driver.find_elements(By.XPATH, "//*[@id=\"description-inline-expander\"]/yt-attributed-string/span"):
            description_span = driver.find_element(By.XPATH, "//*[@id=\"description-inline-expander\"]/yt-attributed-string/span")
            return description_span.text
        else:
            return "No description available"
    else:
        return "No description available"

# TODO the transcript is currently the raw text, with no timestamps.
def get_transcript(driver):
    # if the description isn't open yet, though it should
    if driver.find_element(By.ID, "expand").is_displayed():
        driver.find_element(By.ID, "expand").click()

    # click on show transcript if exists
    if driver.find_elements(By.XPATH, "//*[@id=\"primary-button\"]/ytd-button-renderer/yt-button-shape/button"):
        transcript_button = driver.find_element(By.XPATH, "//*[@id=\"primary-button\"]/ytd-button-renderer/yt-button-shape/button")
        transcript_button.click()

        try:
            raw_transcript = wait_for(driver, EC.presence_of_element_located((By.ID, "segments-container")))
            transcript_lines = raw_transcript.find_elements(By.TAG_NAME, "yt-formatted-string")
            transcript = " ".join([transcript_line.text for transcript_line in transcript_lines])
        except:
            print("Transcript took too long to load")
            transcript = "Empty"

    else:
        print("No transcript available")
        transcript = "Empty"

    return transcript

def initial_search(driver):
    initial_urls = []
    for word in KEY_WORDS:
        word = word.lower()
        word = word.replace(" ", "+")
        driver.get(f"https://www.youtube.com/results?search_query={word}")

        # if the page is asking for cookie consent, accept it first
        if driver.find_elements(By.TAG_NAME, "ytd-consent-bump-v2-lightbox"):
            print("There is a consent box, accept it")
            accept_cookies(driver)
            time.sleep(10)

        videos_elements = wait_for(driver, EC.presence_of_all_elements_located((By.TAG_NAME, "ytd-video-renderer")))
        count = 0
        for video in videos_elements:
            if count == NUMBER_SEARCH:
                break

            # get the SHORTS tag and skip it
            if "SHORTS" in video.text:
                continue

            url = video.find_element(By.ID, "thumbnail").get_attribute("href")
            initial_urls.append(url)
            print(url)
            count += 1
    return initial_urls


# This gets the v parameter value from the url, the video id
def get_video_id(url):
    parsed = urlparse(url)

    if parsed.netloc in ["www.youtube.com", "youtube.com"]:
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]

    return None


def get_recommended(driver):
    recs_links = []
    try:
        recs = (driver.find_element(By.ID, 'related')
                .find_element(By.ID, 'items')
                .find_elements(By.TAG_NAME, "ytd-compact-video-renderer"))
    except:
        recs = []

    for rec in recs:
        rec_link = rec.find_element(By.ID, 'thumbnail').get_attribute('href')
        recs_links.append(rec_link)
        if len(recs_links) >= NUMBER_RECOMMENDATIONS:
            break

    return list(set(recs_links))


def get_video_data(driver, video_url):
    driver.get(video_url)
    time.sleep(1)

    # if the page is asking for cookie consent, accept it first
    if driver.find_elements(By.TAG_NAME, "ytd-consent-bump-v2-lightbox"):
        print("There is a consent box, accept it")
        accept_cookies(driver)
        # time.sleep(10)

    video_title = get_video_title(driver)
    video_likes = get_likes(driver)
    video_channel = get_channel(driver)
    video_desc = get_description(driver)
    video_transcript = get_transcript(driver)
    video_recs = get_recommended(driver)

    return video_title, video_recs, video_desc, video_likes, video_channel, video_transcript


def main():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=Options())

    graph = nx.DiGraph() # THIS HAS **URL IDS** AS IDS
    visited = set() # THIS IS A SET OF **URLS**
    to_visit = initial_search(driver) # THIS IS A LIST OF **URLS**
    #to_visit = [INITIAL_URL, INITIAL_URL] # testing
    d = 0

    for _ in range(DEPTH):
        to_visit_tmp = []
        print("Depth: ", d)

        for url in to_visit:
            video_id = get_video_id(url)

            # if the video is already visited only get the new recommended videos from it, no need to reload other info
            if video_id in [get_video_id(v) for v in visited]:
                recommendations = get_recommended(driver)
                print("Node already exists:", graph.nodes[video_id]["title"])
            else:
                title, recommendations, description, likes, channel, transcript = get_video_data(driver, url)
                print("Title: ", title)
                graph.add_node(video_id, url=url, title=title, depth=d, description=description, likes=likes, channel=channel, transcript=transcript)

                # print("Recommendations: ", recommendations)
                # print("Description: ", desc)
                # print("Likes: ", likes)
                # print("Channel: ", channel)
                # print("Transcript: ", transcript)

            for recommendation in recommendations:
                rec_id = get_video_id(recommendation)
                graph.add_edge(video_id, rec_id)
                if recommendation not in visited:
                    to_visit_tmp.append(recommendation)

            visited.add(url)

        d += 1
        to_visit = to_visit_tmp

    # This is to avoid empty nodes at the end
    print("Videos that still need to be visited:")
    print(to_visit)
    for recommendation in to_visit:
        driver.get(recommendation)
        time.sleep(3)
        video_id = get_video_id(recommendation)
        title = get_video_title(driver)
        desc = get_description(driver)
        likes = get_likes(driver)
        channel = get_channel(driver)
        transcript = get_transcript(driver)

        print(title)
        print(recommendation)

        if video_id in [get_video_id(v) for v in visited]:
            print("Node already exists:", graph.nodes[video_id]["title"])
        else:
            graph.add_node(video_id, url=recommendation, title=title, depth=d, description=desc, likes=likes, channel=channel, transcript=transcript)

    driver.quit()

    nx.write_gexf(graph, "graph.gexf")

if __name__ == "__main__":
    main()

