def write_to(name: str, content: list, as_str: bool = False):
    if as_str:
        to_wrtie = "".join(f"{ag}\n" for ag in content)
    else:
        to_wrtie = {num: agent for num, agent in enumerate(content)}
    with open(name, 'w') as f:
        f.write(to_wrtie)
