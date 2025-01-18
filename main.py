import asyncio
from googletrans import Translator
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import time
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_articles():

    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    driver = webdriver.Chrome(options=options)

    # Create directory to save images
    output_dir = "downloaded_images"
    os.makedirs(output_dir, exist_ok=True)
    try:
        driver.get("https://elpais.com/")
        wait = WebDriverWait(driver, 10)

        # Navigate to the Opinion section
        opinion_section = driver.find_element(By.LINK_TEXT, "Opinión")
        opinion_section.click()
        time.sleep(2)

        # Wait for articles to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))

        articles = driver.find_elements(By.CSS_SELECTOR, "article")[:5]
        articles_contents = []

        for index, article in enumerate(articles, start=1):
            try:
                # Find title
                title_element = article.find_element(By.CSS_SELECTOR, "h2.c_t a")
                title = title_element.text.strip()
                url = title_element.get_attribute('href')

                # Find content
                try:
                    content = article.find_element(By.CSS_SELECTOR, "p.c_d").text.strip()
                except:
                    content = "Content not found"

                # Locate image inside <figure> tag
                try:
                    image_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "figure.c_m img")))
                    image_url = image_element.get_attribute('src')  # Get the main image URL

                    if image_url:
                        # Download and save the image
                        image_name = f"article_{index}.jpg"
                        image_path = os.path.join(output_dir, image_name)

                        response = requests.get(image_url, stream=True)
                        if response.status_code == 200:
                            with open(image_path, "wb") as file:
                                for chunk in response.iter_content(1024):
                                    file.write(chunk)
                except:
                    print("⚠️ Image not found")

                articles_contents.append({
                                'title': title,
                                'content': content,
                                # 'Image URL': image_url,
                                # 'url': url
                            })

                print(f"Title: {title}\nContent: {content}\n")

            except Exception as e:
                print(f"Error processing article: {e}")

    finally:
        driver.quit()
        return articles_contents


async def translate_titles(articles):
    translator = Translator()
    translated_titles = []
    try:
        for article in articles:
            translated = await translator.translate(article['title'], src='es', dest='en')
            article['translated_title'] = translated.text
            translated_titles.append(translated.text)
        return translated_titles
    except Exception as e:
        print(f"Error in translation: {e}")
        return []

def analyze_repeated_words(translated_titles):
    words = ' '.join(translated_titles).split()
    word_counts = Counter(words)
    repeated_words = {word: count for word, count in word_counts.items() if count > 2}
    return repeated_words


async def main():
    # Step 1: Scrape articles
    articles = scrape_articles()

    if not articles:
        print("No articles found.")
        return

    # Step 2: Translate titles to English
    translated_titles = await translate_titles(articles)

    # Step 3: Analyze translated titles for repeated words
    repeated_words = analyze_repeated_words(translated_titles)

    # Output results
    print("Translated Titles:")
    for article in articles:
        print(f"Original: {article['title']}")
        print(f"Translated: {article.get('translated_title', 'No translation available')}\n")

    print("Repeated Words in Titles:", repeated_words)

if __name__ == "__main__":
    asyncio.run(main())

