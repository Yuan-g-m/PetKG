
import requests
from bs4 import BeautifulSoup
import pandas as pd


def fetch_recipes(url):
    """抓取宠物食谱菜单列表"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    result = []
    main_div = soup.find("div", class_="p_content")
    if not main_div:
        print("未找到主内容区块")
        return result

    current_category = None       # 食谱大类，如“犬类食谱”
    current_subcategory = None    # 功效分类，如“美毛亮肤”

    for tag in main_div.find_all(["h2", "strong", "a"]):
        if tag.name == "h2":
            current_category = tag.text.strip()
        elif tag.name == "strong":
            current_subcategory = tag.text.strip()
        elif tag.name == "a" and tag.get("href", "").startswith("/wiki/"):
            recipe_name = tag.text.strip()
            recipe_url = tag["href"]
            result.append([
                recipe_name,
                current_subcategory,
                current_category,
                recipe_url
            ])
    return result


if __name__ == "__main__":
    url = "https://pet.baike.com/wiki/宠物食谱"
    data = fetch_recipes(url)

    df = pd.DataFrame(data, columns=["食谱名称", "功效分类", "食谱大类", "相对链接"])
    df["完整链接"] = "https://pet.baike.com" + df["相对链接"]

    df.to_excel("宠物食谱列表.xlsx", index=False)
    print("已成功保存为：宠物食谱列表.xlsx")
