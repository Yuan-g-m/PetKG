
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


def fetch_food_details(url):
    """抓取单个宠物食品详情页"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1", class_="p_title")
    title_text = title_tag.get_text(strip=True) if title_tag else "未知标题"

    main_div = soup.select_one(".p_main_container")
    if not main_div:
        print(f"❌ 未找到正文区域：{url}")
        return None, None

    content_lines = []

    for tag in main_div.find_all(["h1", "h2", "h3", "p", "ul", "ol", "div"]):
        if tag.name in ["p", "h2", "h3"]:
            text = tag.get_text(separator="", strip=True)
            if text:
                content_lines.append(text)
        elif tag.name in ["ul", "ol"]:
            for li in tag.find_all("li", recursive=False):
                li_text = li.get_text(separator="", strip=True)
                if li_text:
                    content_lines.append(f"- {li_text}")

    content_lines = [line for line in content_lines if line.strip()]
    full_text = f"【食品名称】{title_text}\n" + "\n".join(content_lines)

    return title_text, full_text


def batch_fetch_from_excel(excel_path, overwrite=False):
    df = pd.read_excel(excel_path)
    output_dir = "宠物食品"
    os.makedirs(output_dir, exist_ok=True)

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="📦 抓取宠物食品内容"):
        food_name = str(row["食品名称"]).strip()
        food_url = str(row["完整链接"]).strip()

        safe_title = food_name.replace("/", "_")
        filepath = os.path.join(output_dir, f"{safe_title}.txt")

        if os.path.exists(filepath) and not overwrite:
            tqdm.write(f"⏩ 已存在，跳过：{safe_title}.txt")
            continue

        try:
            title, content = fetch_food_details(food_url)
            if content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                tqdm.write(f"✅ 保存成功：{safe_title}.txt")
            else:
                tqdm.write(f"⚠️ 内容为空：{food_name}")
        except Exception as e:
            tqdm.write(f"❌ 出错：{food_name}，错误信息：{e}")


if __name__ == "__main__":
    batch_fetch_from_excel("宠物食品列表.xlsx", overwrite=False)
