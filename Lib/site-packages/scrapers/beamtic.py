from json import dump
from requests import get
from bs4 import BeautifulSoup


def write_to(name: str, content: list):
    to_wrtie = {num: agent for num, agent in enumerate(content)}
    with open(name, 'w') as f:
        dump(to_wrtie, f, indent=4)


resp = get("https://beamtic.com/user-agents/?browser=FireFox")
soup = BeautifulSoup(resp.text, "html.parser")
agents = []
for agent in soup.find_all("div", attrs={"class": "dk_border dk_pad dk_mar"}):
    agents.append(agent.text.split(": ")[1])
write_to("FakeAgent/data/firefox.json", agents)
