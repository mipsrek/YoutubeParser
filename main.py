from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import networkx as nx
from selenium.webdriver.ie.service import Service
from webdriver_manager.chrome import ChromeDriverManager

INITIAL_URL = "https://www.youtube.com/watch?v=XpkOPlZyFW8"

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=Options())

def get_video_title(video_url):
    driver.get(video_url)
    time.sleep(3)
    try:
        video_title = (driver
                       .find_element(By.ID, "title")
                       .find_element(By.TAG_NAME, "yt-formatted-string").text)
    except:
        video_title = "**Empty**"

    return video_title


def get_video_title_and_rec(video_url):
    video_title = get_video_title(video_url)

    recs_links = []
    recs = (driver.find_element(By.ID, 'related')
            .find_element(By.ID, 'items')
            .find_elements(By.TAG_NAME, "ytd-compact-video-renderer"))

    for rec in recs:
        rec_link = rec.find_element(By.ID, 'thumbnail').get_attribute('href')
        recs_links.append(rec_link)
        if len(recs_links) >= 3:
            break

    return video_title, list(set(recs_links))


def main():
    graph = nx.DiGraph()
    visited = set()
    to_visit = [INITIAL_URL]

    depth = 20
    for _ in range(depth):
        if not to_visit:
            break
        current = to_visit.pop(0)
        if current in visited:
            continue

        title, recommendations = get_video_title_and_rec(current)
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
        title = get_video_title(recommendation)
        graph.add_node(recommendation, title=title)

    driver.quit()

    nx.write_gexf(graph, "graph.gexf")

if __name__ == "__main__":
    main()

