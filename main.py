from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import networkx as nx
from selenium.webdriver.ie.service import Service
from webdriver_manager.chrome import ChromeDriverManager

INITIAL_URL = "https://www.youtube.com/watch?v=U2Fjfqm-7g8"
DEPTH = 20
NUMBER_RECOMMENDATIONS = 3


def accept_cookies(driver):
    driver.find_element(By.XPATH, "//*[@id=\"content\"]/div[2]/div[6]/div[1]/ytd-button-renderer[2]/yt-button-shape/button").click()
    print("Accepted cookies")

def get_video_title(driver):
    try:
        video_title = (driver
                       .find_element(By.ID, "title")
                       .find_element(By.TAG_NAME, "yt-formatted-string").text)
    except:
        video_title = "**Empty**"

    return video_title

# TODO get comments under video
def get_comments(driver):
    driver.execute_script("window.scrollTo(0, 600);")
    time.sleep(3)

    comments = driver.find_element(By.ID, "comments").find_elements(By.ID, "contents")

# TODO get likes of video
def get_likes(driver):
    return None

#TODO get video description
def get_description(driver):
    return None

def get_video_title_and_rec(driver, video_url):
    driver.get(video_url)
    time.sleep(3)

    # if the page is asking for cookie consent, accept it first
    if driver.find_elements(By.TAG_NAME, "ytd-consent-bump-v2-lightbox"):
        print("There is a consent box, accept it")
        accept_cookies(driver)

    time.sleep(5)

    video_title = get_video_title(driver)

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

    return video_title, list(set(recs_links))


def main():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=Options())

    graph = nx.DiGraph()
    visited = set()
    to_visit = [INITIAL_URL]

    for _ in range(DEPTH):
        if not to_visit:
            break
        current = to_visit.pop(0)
        if current in visited:
            continue

        title, recommendations = get_video_title_and_rec(driver, current)
        print(title)
        print(recommendations)

        graph.add_node(current, title=title)
        for recommendation in recommendations:
            graph.add_edge(current, recommendation)
            if recommendation not in visited:
                to_visit.append(recommendation)

        visited.add(current)

    print(to_visit)
    for recommendation in to_visit:
        driver.get(recommendation)
        time.sleep(3)
        title = get_video_title(driver)
        graph.add_node(recommendation, title=title)

    driver.quit()

    nx.write_gexf(graph, "graph.gexf")

if __name__ == "__main__":
    main()

