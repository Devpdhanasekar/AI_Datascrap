import requests
from bs4 import BeautifulSoup
import os

# URL to scrape
url = "https://vivartana.in/"

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract all text data
    text_data = soup.get_text(separator='\n', strip=True)
    print("Text Data:\n", text_data)
    
    # Extract all image URLs
    img_tags = soup.find_all('img')
    img_urls = [img['src'] for img in img_tags if 'src' in img.attrs]
    
    print("\nImage URLs:")
    for img_url in img_urls:
        print(img_url)
    
    # Optionally, download images
    os.makedirs('downloaded_images', exist_ok=True)
    
    for idx, img_url in enumerate(img_urls):
        if not img_url.startswith(('http://', 'https://')):
            img_url = url + img_url
        
        img_response = requests.get(img_url)
        if img_response.status_code == 200:
            with open(f'downloaded_images/image_{idx + 1}.jpg', 'wb') as f:
                f.write(img_response.content)
else:
    print(f"Failed to retrieve the web page. Status code: {response.status_code}")
