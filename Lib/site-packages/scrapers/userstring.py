# Copyright (c) 2022 Itz-fork

from json import dump
from requests import get
from bs4 import BeautifulSoup


BROWSERS = ["Chrome", "Firefox", "Edge", "Opera", "Safari", "Internet Explorer"]


def write_to(name: str, content: list):
    to_wrtie = {num: agent for num, agent in enumerate(content)}
    with open(name, 'w') as f:
        dump(to_wrtie, f, indent=4)

def scrape_uas(browser):
    resp = get(f"http://useragentstring.com/pages/useragentstring.php?name={browser}")
    soup = BeautifulSoup(resp.text, "html.parser")
    agents = []

    for ul in soup.find_all("div", attrs={"id": "liste"}):
        for li in ul.find_all("ul"):
            for item in li.find_all("li"):
                agents.append(item.text)
    return agents


for brow in BROWSERS:
    write_to("FakeAgent/data/{}.json".format(brow.replace(" ", "")), scrape_uas(brow))