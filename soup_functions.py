def h1_left_align(soup):
    for tag in soup.find_all("h1"):
        tag['style'] = "text-align: left;"


def responsive_images(soup):
    for tag in soup.find_all("img"):
        tag['style'] = "max-width: 100%; height: auto;"


def remove_scripts(soup):
    soup.script.decompose()
