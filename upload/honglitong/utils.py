def parse_html_options(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'lxml')
    options = soup.find_all('dd')
    result = {}
    for option in options:
        value = option.get('lay-value')
        if not value:
            continue

        text = option.text.strip()
        result[text] = {
            'level': value,
            'children': []
        }
    return result
