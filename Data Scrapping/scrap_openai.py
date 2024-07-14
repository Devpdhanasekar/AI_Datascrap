import requests
from bs4 import BeautifulSoup
import openai
import json

# Set up your OpenAI API key
openai.api_key = "sk-proj-J8XM9bjsLMKJQsWvxxbAT3BlbkFJKK7PYvsmQYtkI6gFDbP0"
# sk-proj-YmhPmQOhebJzha4kdaQET3BlbkFJj6RDRpXKWi1F7j3P4G84

def scrape_fund_data(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve the web page. Status code: {response.status_code}")
        return None

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract the text content of the page
    text_data = soup.get_text(separator='\n', strip=True)
    
    return text_data

def process_with_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the new model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def main(url):
    # Step 1: Scrape data from the website
    scraped_data = scrape_fund_data(url)
    print(scraped_data)
    if scraped_data is None:
        print("Scraping failed.")
        return "Scraping failed."

    # Step 2: Prepare a prompt for OpenAI model
    prompt = f"""{scraped_data} 
             The objective of you is to create a complete and accurate JSON output based on the web-scraped details stored in the variable webScarp. The JSON output should fill all the keys provided in the template with relevant information extracted from webScarp. The goal is to generate a comprehensive and informative JSON representation of the company's details.
Step 1: Analyze the Web-Scraped Details
Analyze the web-scraped details stored in the variable webScarp. This string contains information about a company.
Step 2: Identify Relevant Information
Identify the relevant information within webScarp that corresponds to the keys in the given JSON content.
Step 3: Fill JSON Keys
Fill the JSON keys with non-empty values extracted from webScarp. Ensure that all keys are filled with accurate and relevant information.
Step 4: Create Complete JSON Output
Create a complete and accurate JSON output by filling all the keys with non-empty values.
Do Not Leave Any Values Empty
Do not leave any values empty. Fill all the keys with relevant information from webScarp.
Follow These Steps Exactly
Follow these steps exactly to generate the JSON output. Do not deviate from the instructions or make any assumptions.
JSON Template
The JSON template is as follows:
json
    "Fund Name": "",
    "Brief Description": "",
    "HQ Location": "",
    "Investor Type": "",
    "Stages of Entry/ Investment": "",
    "Sectors of Investment": "",
    "Geographies Invested In": "",
    "Portfolio Companies": "",
    "No.of Exits": "",
    "Website": "",
    "Portfolio Unicorns / Soonicorns": "",
    "Portfolio Exits": "",
    "Deals in last 12 months": "",
    "Size of the Fund": "",
    "Founded Year": "",
    "LinkedIn": "",
    "Founders": "",
    "Tags/ Keywords": ""
Fill the JSON Keys
Fill the JSON keys with non-empty values extracted from webScarp. Ensure that all keys are filled with accurate and relevant information.

Note
Ensure that all keys are filled with non-empty values. and must return a response as json format only won't and any extra data into that if you add any extra data into json like ```json my labtop wil burn"""

    print("xcvbnxcvbnxcvbxcvbnm",prompt)


    # Step 3: Use OpenAI model to process the data
    processed_data = process_with_openai(prompt)
    start = processed_data.find("{")
    end = processed_data.find("}")
    
    print("answer", (processed_data))
    return {"result": json.loads(processed_data)}

if __name__ == "__main__":
    url = "https://ventureintelligence.com/"  # Replace with the actual URL
    main(url)
