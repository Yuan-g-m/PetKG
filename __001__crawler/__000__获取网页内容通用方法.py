
import requests
from bs4 import BeautifulSoup


def fetch_pet_details(url):
    """通用的宠物百科网页内容抓取方法"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    print(response.text)


if __name__ == "__main__":
    fetch_pet_details("https://pet.baike.com/wiki/宠物食谱")
