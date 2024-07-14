from flask import Flask, jsonify, request
# from scrap_openai import main
import requests
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import openai
import json
# from helper import dbCommunication
from tavily import TavilyClient
from pymongo import MongoClient
from bson.json_util import dumps

# Create Flask application
app = Flask(__name__)
CORS(app)



from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError



# @app.route('/getInvestors', methods=['GET'])
# def getInvestors():
#     query = "select * from investment_funds"
#     finalData = dbCommunication(query)
#     return {"data": finalData}


def getFounderLinkedIn(query, location="United States"):
    url = "https://serpapi.com/search"
    
    # Define the parameters for the API request
    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "num": 1,  # Request only the top result
        "api_key": "ffa8d2e78d043faf183d3de8c8b72476feedb90d7486d03bbff755de735e55f5"
    }
    
    # Make the request to the SERP API
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response
        if 'organic_results' in data and len(data['organic_results']) > 0:
            print(data['organic_results'][0])
            return data['organic_results'][0]  # Return the top result
        else:
            return None  # No organic results found
    else:
        return None 

tavily = TavilyClient(api_key="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")
    
# @app.route('/fundSize',methods=["POST"])
def tavily_search(query):
    url = "https://api.tavily.com/search"
    # url = request.get_json()
    print(url)
    qna_response = tavily.qna_search(query=query)
    return{"response":qna_response}
    # Construct the payload
    # payload = {
    #     "api_key": "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",
    #     "query": url["query"],
    #     "search_depth": "advanced",
    #     "include_answer": True,
    #     "include_images": False,
    #     "include_raw_content": True,
    #     "max_results": 1,
    #     "include_domains":[],
    #     "exclude_domains": []
    # }
    
    # # Send the POST request to the API
    # response = requests.post(url, json=payload)
    
    # # Handle potential errors
    # if response.status_code == 200:
        # return response.json()
    
    # else:
        # return {
        #     "error": response.status_code,
        #     "message": response.text
        # }




def get_lat_long(location):
    geolocator = Nominatim(user_agent="my_app")
    
    try:
        # Attempt to geocode the location
        location_info = geolocator.geocode(location)
        
        if location_info:
            latitude = location_info.latitude
            longitude = location_info.longitude
            return {latitude, longitude}
        else:
            return "Location not found"
    
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return f"Error: {str(e)}"



def parse_results(data):
    if not data:
        return []

    # results = data.get('local_results', [])
    parsed_results = []

    for place in data:
        parsed_results.append({
            'name': place.get('title'),
            'address': place.get('address'),
            'phone': place.get('phone'),
            'rating': place.get('rating'),
            'reviews': place.get('reviews'),
            'price': place.get('price'),
            'type': place.get('type'),
            'website': place.get('website'),
            'open_state': place.get('open_state'),
            'hours': place.get('hours'),
            'gps_coordinates': place.get('gps_coordinates'),
            'thumbnail': place.get('thumbnail')
        })

    return parsed_results




def scrape_google_maps(api_key, query, count, lattitude, longitude):
    location = f"@{lattitude},{longitude},{15.1}z"
    all_results = []
    
    for page in range(count):  # Scrape 3 pages
        params = {
            "api_key": api_key,
            "engine": "google_maps",
            "q": query,
            "ll": location,
            "type": "search",
            "start": page * 20  # Each page typically has 20 results
        }
        
        response = requests.get('https://serpapi.com/search', params=params)
        data = response.json()
        
        if 'local_results' in data:
            results = data['local_results']
            all_results.extend(results)
        
        if 'serpapi_pagination' not in data or not data['serpapi_pagination'].get('next'):
            break  # No more pages to scrape
    
    return all_results




@app.route('/googlemap', methods=["POST"])
def getGoogleMapData():
    print("dfghjkafghjkadfghjkafghjkadfghjkadfghjkdfghjaaaaaaaaaaaaaaafghjk")
    url = request.get_json()
    print(url)
    api_key = "ffa8d2e78d043faf183d3de8c8b72476feedb90d7486d03bbff755de735e55f5"  # Replace with your actual SerpApi key
    location = url["location"]
    query = url["query"]
    pagination_count = url["pageCount"] * 20
    print(pagination_count)
    
    lat, long = get_lat_long(location)

    results = scrape_google_maps(api_key, query, pagination_count, lat, long)
    data = parse_results(results)
    
    
    return {"result":results}

@app.route('/investment', methods=["GET"])
def getInvestmentData():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['crafy_db']
        collection = db['investment_funds']
        # investment_data = collection.find()
        # print(investment_data)
        # return {"data":jsonify(list(investment_data))}
        data = collection.find()
        # Convert the cursor to a list of documents
        data_list = list(data)
        # Convert the list to JSON
        response = dumps(data_list)
        return response, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return f"Error: {str(e)}"



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
        print(response.choices[0].message['content'].strip())
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/webscrap', methods=["POST"])
def scrapDataFromWeb():
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['crafy_db']
        collection = db['investment_funds']

        # Check if the data already exists
        url_data = request.get_json()
        website_url = url_data["url"]["website"]
        isAvailable = collection.find_one({"website": website_url})
        
        if isAvailable:
            return {"message": "Data already exists"}

        # Proceed with scraping if data does not exist
        raw_data = scrape_fund_data(website_url)
        prompt = f"""
            {raw_data}
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
            "Equity / Debt (Fund Category)":"",
            "Stages of Entry/ Investment": "",
            "Sectors of Investment": "",
            "Geographies Invested In": "",
            "Portfolio Companies": "",
            "No.of Portfoilo Companies Invested in" : "",
            "No.of Exits": "",
            "Portfolio Acquisitions": "",
            "Website": "",
            "Portfolio Unicorns / Soonicorns": "",
            "Portfolio Exits": "",
            "Operating Status (Active/ Deadpooled/ etc)" : "",
            "Deals in last 12 months": "",
            "AUM (Dollar)": "",
            "Size of the Fund": "",
            "Founded Year": "",
            "Team size": "",
            "Group Email ID/ Email ID" : "",
            "Contact Number": "",
            "LinkedIn": "",
            "Twitter": "",
            "Youtube" : "",
            "Co-Investors": "",
            "Founders": "",
            "Tags/ Keywords": ""
        """

        print("Prompt for OpenAI:", prompt)

        # Step 3: Use OpenAI model to process the data
        processed_data = process_with_openai(prompt)
        start = processed_data.find("{")
        end = processed_data.find("}")
        processed_data = processed_data[start:end+1]
        finalResult = json.loads(processed_data)

        # Construct the data for MongoDB
        data = {
            'fund_name': url_data["url"]["title"],
            'brief_description': finalResult.get("Brief Description", ""),
            'hq_location': finalResult.get("HQ Location", ""),
            'investor_type': url_data["url"]["type"],
            'equity_debt_fund_category': finalResult.get("Equity / Debt (Fund Category)", ""),
            'stages_of_entry_investment': finalResult.get("Stages of Entry/ Investment", ""),
            'sectors_of_investment': finalResult.get("Sectors of Investment", ""),
            'geographies_invested_in': finalResult.get("Geographies Invested In", ""),
            'portfolio_companies': finalResult.get("Portfolio Companies", ""),
            'no_of_portfolio_companies_invested_in': finalResult.get("No.of Portfoilo Companies Invested in", ""),
            'no_of_exits': finalResult.get("No.of Exits", ""),
            'portfolio_acquisitions': finalResult.get("Portfolio Acquisitions", ""),
            'website': website_url,
            'portfolio_unicorns_soonicorns': finalResult.get("Portfolio Unicorns / Soonicorns", ""),
            'portfolio_exits': finalResult.get("Portfolio Exits", ""),
            'operating_status_active_deadpooled_etc': finalResult.get("Operating Status (Active/ Deadpooled/ etc)", ""),
            'deals_in_last_12_months': finalResult.get("Deals in last 12 months", ""),
            'size_of_the_fund': finalResult.get("Size of the Fund", ""),
            'aum_dollar': finalResult.get("AUM (Dollar)", ""),
            'founded_year': finalResult.get("Founded Year", ""),
            'team_size': finalResult.get("Team Size", ""),
            'group_email_id_email_id': finalResult.get("Group Email ID/ Email ID", ""),
            'contact_number': finalResult.get("Contact Number", ""),
            'linkedin': finalResult.get("LinkedIn", ""),
            'twitter': finalResult.get("Twitter", ""),
            'youtube': finalResult.get("Youtube", ""),
            'co_investors': finalResult.get("Co-Investors", ""),
            'founders': finalResult.get("Founders", ""),
            'tags_keywords': finalResult.get("Tags/ Keywords", "")
        }

        inserted_id = collection.insert_one(data).inserted_id

        # Additional data fetching and updating if necessary
        if not data['size_of_the_fund']:
            fundSize = tavily_search(url_data["url"]["title"] + " company overall fund size")
            collection.update_one({'_id': inserted_id}, {'$set': {'size_of_the_fund': fundSize["response"]}})

        if not data['linkedin']:
            founderLinkedIn = getFounderLinkedIn(url_data["url"]["title"] + " company founder linkedin profile")
            collection.update_one({'_id': inserted_id}, {'$set': {'linkedin': founderLinkedIn}})

        if not data['deals_in_last_12_months']:
            lastDeals = tavily_search(url_data["url"]["title"] + " last 12 months funding deals")
            collection.update_one({'_id': inserted_id}, {'$set': {'deals_in_last_12_months': lastDeals["response"]}})

        if not data['founders'] or not data['co_investors'] or not data['team_size'] or not data['portfolio_acquisitions'] or not data['portfolio_unicorns']:
            additionalDetails = tavily_search(url_data["url"]["title"] + " Give me a json data for this, This json will contains founders,co_investors,team_size,portfolio_acquisition: in details of portfolio,portfolio_unicorns: in details of unicorns,stages_of_entry_investment,sectors_of_investment")
            myJson = json.loads(additionalDetails["response"])
            collection.update_one({'_id': inserted_id}, {'$set': {
                'founders': myJson["founders"],
                'co_investors': myJson["co_investors"],
                'team_size': myJson["team_size"],
                'portfolio_acquisitions': myJson["portfolio_acquisitions"],
                'portfolio_unicorns': myJson["portfolio_unicorns"],
                'stages_of_entry_investment': myJson["stages_of_entry_investment"],
                'sectors_of_investment': myJson["sectors_of_investment"]
            }})

        # Return a JSON response with the inserted_id
        return jsonify({'inserted_id': str(inserted_id)})

    except Exception as error:
        return f"Error: {str(error)}"

# def scrapDataFromWeb():
#     try:
#         client = MongoClient('mongodb://localhost:27017/')
#         db = client['crafy_db']
#         collection = db['investment_funds']
#         isAvailable = collection.find_one({"website": request.json["url"]["website"]})
#         if isAvailable:
#             return {"message": "Data already exists"}
#         else:
#             url = request.get_json()
#             print(url)
#             raw_data = scrape_fund_data(url["url"]["website"])
#             prompt = f"""{raw_data} 
#                     The objective of you is to create a complete and accurate JSON output based on the web-scraped details stored in the variable webScarp. The JSON output should fill all the keys provided in the template with relevant information extracted from webScarp. The goal is to generate a comprehensive and informative JSON representation of the company's details.
#         Step 1: Analyze the Web-Scraped Details
#         Analyze the web-scraped details stored in the variable webScarp. This string contains information about a company.
#         Step 2: Identify Relevant Information
#         Identify the relevant information within webScarp that corresponds to the keys in the given JSON content.
#         Step 3: Fill JSON Keys
#         Fill the JSON keys with non-empty values extracted from webScarp. Ensure that all keys are filled with accurate and relevant information.
#         Step 4: Create Complete JSON Output
#         Create a complete and accurate JSON output by filling all the keys with non-empty values.
#         Do Not Leave Any Values Empty
#         Do not leave any values empty. Fill all the keys with relevant information from webScarp.
#         Follow These Steps Exactly
#         Follow these steps exactly to generate the JSON output. Do not deviate from the instructions or make any assumptions.
#         JSON Template
#         The JSON template is as follows:
#         json

#             "Fund Name": "",
#             "Brief Description": "",
#             "HQ Location": "",
#             "Investor Type": "",
#             "Equity / Debt (Fund Category)":"",
#             "Stages of Entry/ Investment": "",
#             "Sectors of Investment": "",
#             "Geographies Invested In": "",
#             "Portfolio Companies": "",
#             "No.of Portfoilo Companies Invested in" : "",
#             "No.of Exits": "",
#             "Portfolio Acquisitions": "",
#             "Website": "",
#             "Portfolio Unicorns / Soonicorns": "",
#             "Portfolio Exits": "",
#             "Operating Status (Active/ Deadpooled/ etc)" : "",
#             "Deals in last 12 months": "",
#             "AUM (Dollar)": "",
#             "Size of the Fund": "",
#             "Founded Year": "",
#             "Team size": "",
#             "Group Email ID/ Email ID" : "",
#             "Contact Number": "",
#             "LinkedIn": "",
#             "Twitter": "",
#             "Youtube" : "",
#             "Co-Investors": "",
#             "Founders": "",
#             "Tags/ Keywords": "",

#         ### Important Note
#         The model should give only the JSON as output. No additional details or information should be present in the response,Must follow this If any data in not provided then you need assign an empty string against to that field, only the JSON should be there.

#         ### Fill the JSON Keys
#         Fill the JSON keys with non-empty values extracted from webScarp. Ensure that all keys are filled with accurate and relevant information.
#         ### consider this as example 

#         "Fund Name": "Blume Ventures",
#         "Brief Description": "Blume is an early stage venture fund that backs startups with both funding as well as active mentoring. We typically invest in tech-led startups, led by founders who are obsessed with solving hard problems, uniquely Indian in nature, and impacting large markets. Our vision is to be the leading platform that sources, funds, nurtures and creates value for India's brightest young startups – helping them 'blume'!",
#         "HQ Location": "Mumbai",
#         "Investor Type": "Venture Capital",
#         "Equity / Debt (Fund Category)": "Equity",
#         "Stages of Entry/ Investment": "Early Stage, Growth stage, IPO, Unicorn",
#         "Sectors of Investment": "60-65 percentage of the new fund in domestic-heavy sectors such as healthcare, financial services, commerce and brands, jobs and education, and digital media and gaming. The other 35-40% of the fund will focus on SaaS, and DeepTech (including CleanTech, manufacturing, blockchain) companies, typically in B2B\n\nEV & Mobility, ClimateTech, B2B Services, SMB, SaaS, Media, Entertainment & Gaming, Consumer Tech, Ari Tech, Artificial Intellgence,  B2B Commerce and Marketplaces, Consumer Brands, Consumer Services, Commerce Enabler, Consumer Tech, Deep Tech, Ed Tech, Fin Tech, Food Tech, HR Tech, Healthcare, ITSM, Infrastructure Saas and Dev Tools, Logistics, Real Estate, Sustainability",
#         "Geographies Invested In": "Bengaluru, Chennai, Hyderabad, Mumbai, Vijayawada, Delhi NCR, Pune, Singapore, UK, Canada, UAE, USA",
#         "Portfolio Companies": "Jai Kisan, Niqo Robotics, Stellapps, Atomic Work, Aerem, ApnaKlub, Bambrew, Cashify, Classplus, Manufactured, Procol, Spinny, Battery Smart, BHIVE Workspace, Dunzo, E2E Networks, Ethereal Machines, Exotel, Finvolv, Futwork, HealthAssure, IDfy, Infollion, InTouchApp, Kaliedofin, LeadCandy, Leverage Edu, Printo, Qyuki, Redquanta, Rocketium, Routematic, Runnr, Smartstaff, SquadStack, THB, Tricog, Tripvillas, WebEngage, Yulu, Zip Dial, Zopper, Ati Motors, Carbon Clean, ElectricPe, Euler Motors, Vecmocon Technologies, Flash, Freakins, LLB, Milkbakset, Promptec, Purplle, SuperK, Ultrahuman, DataWeave, Futwork, Instamojo, LoveLocal, NowFloats, Snapbizz, The Wedding Brigade, Uniqode, BillBachao, HealthifyMe, IntrCity, Leverage Edu, Medfin, Multipl, Slice, smallcase, Stage 3, Trip Villas, Unacademy, Unocoin, Uolo, Virohan, Accio, Adepto, AutoVerse, BeatO, Glamrs, iService, Koo, Stage, Taaraka, WeAreHolidays, Wiom, Agara Labs, GreyOrange, Locus, Pixxel, Systemantics, Tookitaki, Tricog, Zenatix, Taxiforsure, Alippo, Classplus, Mastree, Mockbank, Oheyo, Virohan, Bluecopa, Bureau, Chaitanya, Chillr, Clink, DPDZero, Finvolv, Moneysights, Mysa, Optimo, PrivateCircle, Qubecell, Servify, Turtlemint, Zoppor, ChefKart, GreyHR, Interview Kickstart, Mettl, Rizort, Skillenza, Smartstaff, Superset, TapChief, HealthAssure, Hybrent, Karmic, Ultrahuman, 1Click, Frambench, InTouchApp, LambdaTest, Minjar, Scribble Data, Sift Hub, Sprinto, Uniqode, Zapccale, Zipy, Atomicwork, Patch, Sprinto, Valgen, Pico Xpress, Hashcube, Koo, MechMocha, Rolocule, Stage, StrmEasy, Salty, Fastfox, Hotelogix, Hybrent, Threadsol, Wiz Commerce",
#         "No. of Portfolio Companies Invested in": '160',
#         "No.of Exits": '39',
#         "Portfolio Acquisitions": "Agara Labs, Chillr, Hybrent, Mettl, Minjar, Promptec, Runnr, Superset, Taxi for sure, Threadsol, ZipDial, 1click, Bill Bachao, Chaitanya, Framebench, iService, Mastree, MilkBasket, Nowfloats, Qubecell, StrmEasy, TapChief, Zenatix, Adepto, Clink (Gharpay), Fastfox, Glamrs, Karmic, LBB, MechMocha, MockBank, Moneysights, Patch, Rolocule, Valgen Infosys, We are Holidays",
#         "Website": "https://blume.vc/",
#         "Portfolio Unicorns / Soonicorns": "Unicorns - Spinny, Purplle, slice, Unacademy",
#         "Portfolio Exits": "Agara Labs, Chillr, E2E Networks, Hybrent, Infollion, Mettl, Minjar, Promptec, Runnr, Superset, Taxi for sure, Threadsol, Uniqode, ZipDial, 1click,Bill Bachao, Chaitanya, Framebench, iService, Mastree, MilkBasket, Nowfloats, Qubecell, StrmEasy, TapChief, Zenatix, Adepto, Clink (Gharpay), Fastfox, Glamrs, Karmic, LBB, MechMocha, MockBank, Moneysights, Patch, Rolocule, Valgen Infosys, We are Holidays",
#         "Operating Status (Active/ Deadpooled, etc)": "Active",
#         "Deals in last 12 months": "Atomicwork, Flash, DPDzero, Zivy, PicoXpress, Bambrew, SuperK, Optimo Capital, Interview Kickstart",
#         "AUM $$": "Fund VI (2021 onwards) - $290M",
#         "Size of the Fund": "$1.5 to $3m (₹12 to 24 crs), 12-20 percentage stake",
#         "Founded Year": '2011',
#         "Team Size": '46',
#         "Group Email ID/ Email ID": "contact@blume.vc",
#         "Contact Number": "022-43471659",
#         "LinkedIn": "https://www.linkedin.com/company/blume-venture-advisors/?originalSubdomain=in",
#         "Twitter (X)": "https://x.com/blumeventures",
#         "Youtube": "https://www.youtube.com/channel/UCMVGOgVL6OJyoxWFN1pmLCw",
#         "Co-Investors": "",
#         "Founders": "Sanjay Nath, Karthik Reddy",
#         "Tags/ Keywords": ""

#         """

#             print("xcvbnxcvbnxcvbxcvbnm",prompt)


#             # Step 3: Use OpenAI model to process the data
#             processed_data = process_with_openai(prompt)
#             start = processed_data.find("{")
#             end = processed_data.find("}")
#             # processed_data = processed_data.replace("", "NULL")
            
#             print("answer", (processed_data[start:end+1]))
#             finalResult = json.loads(processed_data[start:end+1])
#             data = {
#             'fund_name': url["url"]["title"],
#             'brief_description': finalResult.get("Brief Description", "ON"),
#             'hq_location': finalResult.get("HQ Location", "ON"),
#             'investor_type': url["url"]["type"],
#             'equity_debt_fund_category': finalResult.get("Equity / Debt (Fund Category)", "ON"),
#             'stages_of_entry_investment': finalResult.get("Stages of Entry/ Investment", "ON"),
#             'sectors_of_investment': finalResult.get("Sectors of Investment", "ON"),
#             'geographies_invested_in': finalResult.get("Geographies Invested In", "ON"),
#             'portfolio_companies': finalResult.get("Portfolio Companies", "ON"),
#             'no_of_portfolio_companies_invested_in': finalResult.get("No.of Portfoilo Companies Invested in", "ON"),
#             'no_of_exits': finalResult.get("No.of Exits", "ON"),
#             'portfolio_acquisitions': finalResult.get("Portfolio Acquisitions", "ON"),
#             'website': url["url"]["website"],
#             'portfolio_unicorns_soonicorns': finalResult.get("Portfolio Unicorns / Soonicorns", "ON"),
#             'portfolio_exits': finalResult.get("Portfolio Exits", "ON"),
#             'operating_status_active_deadpooled_etc': finalResult.get("Operating Status (Active/ Deadpooled/ etc)", "ON"),
#             'deals_in_last_12_months': finalResult.get("Deals in last 12 months", "ON"),
#             'size_of_the_fund': finalResult.get("Size of the Fund", "ON"),
#             'aum_dollar': finalResult.get("AUM (Dollar)", "ON"),
#             'founded_year': finalResult.get("Founded Year", "ON"),
#             'team_size': finalResult.get("Team Size", "ON"),
#             'group_email_id_email_id': finalResult.get("Group Email ID/ Email ID", "ON"),
#             'contact_number': "NULL",
#             'linkedin': finalResult.get("LinkedIn", "ON"),
#             'twitter': finalResult.get("Twitter", "ON"),
#             'youtube': finalResult.get("Youtube", "ON"),
#             'co_investors': finalResult.get("Co-Investors", "ON"),
#             'founders': finalResult.get("Founders", "ON"),
#             'tags_keywords': finalResult.get("Tags/ Keywords", "ON")
#         }
#             inserted_id = collection.insert_one(data).inserted_id
#             size_of_the_fund = data.get('size_of_the_fund')
#             if size_of_the_fund == "NULL" or size_of_the_fund == "" or len(size_of_the_fund) < 10:
#                 fundSize = tavily_search(url["url"]["title"] + " company overall fund size")
#                 print(fundSize)
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'size_of_the_fund': fundSize["response"]}}
#                 )
#             linkedIn = data.get('linkedin')
#             print(linkedIn)
#             if(linkedIn =="" or len(linkedIn) < 10):
#                 print("called")
#                 founderLinkedIn = getFounderLinkedIn(url["url"]["title"]+" company founder linkedin profile")
#                 print(founderLinkedIn)
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'linkedin': founderLinkedIn}}
#                 )
#             deals = data.get('deals_in_last_12_months')
#             print(deals)
#             if (deals == "" or len(deals) < 6):
#                 print("called")
#                 lastDetals = tavily_search(url["url"]["title"]+" last 12 months funding deals")
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'deals_in_last_12_months': lastDetals["response"]}}
#                 )
#                 print("linkedin",lastDetals)
#             founders = data.get('founders')
#             if (founders == "" or len(deals) < 15):
#                 print("called")
#                 lastDetals = tavily_search(url["url"]["title"]+" Give me a json data for this, This json will contains founders,co_investors,team_size,portfolio_acquisition: in details of portfolio,portfolio_unicorns: in details of unicorns,stages_of_entry_investment,sectors_of_investment")
#                 myJson = json.loads(lastDetals["response"])
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'founders': myJson["founders"]}}
#                 )
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'co_investors': myJson["co_investors"]}}
#                 )
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'team_size': myJson["team_size"]}}
#                 )
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'portfolio_acquisition': myJson["portfolio_acquisition"]}}
#                 )
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'portfolio_unicorns': myJson["portfolio_unicorns"]}}
#                 )
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'stages_of_entry_investment': myJson["stages_of_entry_investment"]}}
#                 )
#                 collection.update_one(
#                     {'_id': inserted_id},
#                     {'$set': {'sectors_of_investment': myJson["sectors_of_investment"]}}
#                 )
#                 # myJson = json.loads(myJson)
#                 print("linkedin",myJson)


#             # Return a JSON response with the inserted_id
#             return jsonify({'inserted_id': str(inserted_id)})
#     except Exception as error:
#         return f"Error: {str(error)}"

#     for key in finalResult:
#         if isinstance(finalResult[key], str):
#             finalResult[key] = finalResult[key].replace("not", " ")
#     for key in finalResult:
#         if (finalResult[key] == ""):
#             finalResult[key] = "NULL"
#     for key in finalResult:
#         if isinstance(finalResult[key], str):
#             finalResult[key] = finalResult[key].replace(",", " ")
#     for key in finalResult:
#         if isinstance(finalResult[key], str):
#             finalResult[key] = finalResult[key].replace("'", "''")
#     # print("finalResult",(finalResult.get("Brief Description")))
    
#     query = f"""
#     INSERT INTO investment_funds (
#         fund_name,
#         brief_description,
#         hq_location,
#         investor_type,
#         equity_debt_fund_category,
#         stages_of_entry_investment,
#         sectors_of_investment,
#         geographies_invested_in,
#         portfolio_companies,
#         no_of_portfolio_companies_invested_in,
#         no_of_exits,
#         portfolio_acquisitions,
#         website,
#         portfolio_unicorns_soonicorns,
#         portfolio_exits,
#         operating_status_active_deadpooled_etc,
#         deals_in_last_12_months,
#         size_of_the_fund,
#         aum_dollar,
#         founded_year,
#         team_size,
#         group_email_id_email_id,
#         contact_number,
#         linkedin,
#         twitter,
#         youtube,
#         co_investors,
#         founders,
#         tags_keywords
#     ) VALUES (
#         '{url["url"]["title"]}',
#         '{finalResult.get("Brief Description", "ON")}',
#         '{finalResult.get("HQ Location", "ON")}',
#         '{url["url"]["type"]}',
#         '{finalResult.get("Equity / Debt (Fund Category)", "ON")}
#         '{finalResult.get("Stages of Entry/ Investment", "ON")}',
#         '{finalResult.get("Sectors of Investment", "ON")}',
#         '{finalResult.get("Geographies Invested In", "ON")}',
#         '{finalResult.get("Portfolio Companies", "ON")}',
#         '{finalResult.get("No.of Portfoilo Companies Invested in", "ON")}',
#         '{finalResult.get("No.of Exits", "ON")},
#         '{finalResult.get("Portfolio Acquisitions", "ON")}',
#         '{url["url"]["website"]}',
#         '{finalResult.get("Portfolio Unicorns / Soonicorns", "ON")}',
#         '{finalResult.get("Portfolio Exits", "ON")}',
#         '{finalResult.get("Operating Status (Active/ Deadpooled/ etc)", "ON")}',
#         '{finalResult.get("Deals in last 12 months", "ON")}',
#         '{finalResult.get("Size of the Fund", "ON")}',
#         '{finalResult.get("AUM (Dollar)", "ON")},
#         '{finalResult.get("Founded Year", "ON")}',
#         '{finalResult.get("Team Size", "ON")}',
#         '{finalResult.get("Group Email ID/ Email ID", "ON")}',
#         '{"NULL"}',
#         '{finalResult.get("LinkedIn", "ON")}',
#         '{finalResult.get("Twitter", "ON")}',
#         '{finalResult.get("Youtube", "ON")}',
#         '{finalResult.get("Co-Investors", "ON")},
#         '{finalResult.get("Founders", "ON")}',
#         '{finalResult.get("Tags/ Keywords", "ON")}'
#     )
#     """
#     queryQ = f"""You are an expert in PostgreSQL. Given a SQL query, identify and correct any syntax errors. Provide the corrected query in JSON format. Must return the all columns. Please won't omit and add any new column, if any feild of the query is not available then you need to assign as null and any data is empty then you need assign a null for that field. Here is the query:
#     {query} . You Must need to retrun a json format with the key of query : ""
# """
#     ai_query = process_with_openai(queryQ)
#     ai_start = ai_query.find("{")
#     ai_end = ai_query.find("}")
#     print("newone", query)
#     finalQuey = json.loads(ai_query[ai_start:ai_end+1])
#     print("mylove",finalQuey["query"])
#     myQuery = finalQuey["query"].replace("'s", "s")

#     print(myQuery)

#     inserted = dbCommunication(myQuery,True)
#     print("fghjghjghjkghjkghjkghjkghjk",finalResult)
#     if (finalResult.get("Size of the Fund") == "NULL"):
#         fundSize = tavily_search(url["url"]["title"]+" company fund size")
#         fundSize["response"].replace("'", " ")
#         fundSize["response"].replace("'s", "s")
#         # lastDetals["response"].replace("'", " ")
#         upQuery = f"""
#     update investment_funds
#     SET size_of_the_fund = '{fundSize["response"]}'
#     WHERE fund_name = '{url["url"]["title"]}';
# """
#         updatedData = dbCommunication(upQuery,True)
#         print("updated",fundSize,upQuery)

#     if(finalResult.get("LinkedIn")):
#         founderLinkedIn = getFounderLinkedIn(url["url"]["title"]+" company founder linkedin profile")
#         print(founderLinkedIn)
#         upQuery = f"""
#     update investment_funds
#     SET linkedin = '{founderLinkedIn["link"]}'
#     WHERE fund_name = '{url["url"]["title"]}';
# """
#         updatedData = dbCommunication(upQuery,True)
#         print(founderLinkedIn)
#     if (finalResult.get("Deals in last 12 months")):
#         lastDetals = tavily_search(url["url"]["title"]+" last 12 months funding deals")
#         print("linkedin",lastDetals)
#         lastDetals["response"].replace("'", " ")
#         lastDetals["response"].replace(",", " ")
#         lastDetals["response"].replace("'s", "s")
#         upQuery = f"""
#     update investment_funds
#     SET deals_in_last_12_months = '{lastDetals["response"]}'
#     WHERE fund_name = '{url["url"]["title"]}';
# """
#         updatedData = dbCommunication(upQuery,True)
#         print("deals",lastDetals)
#     if (finalResult.get("Founders") == "NULL"):
#         lastDetals = tavily_search(url["url"]["title"]+" company founder names")
#         print("founders",lastDetals)
#         lastDetals["response"].replace("'", " ")
#         lastDetals["response"].replace(",", " ")
#         lastDetals["response"].replace("'s", "s")
#         upQuery = f"""
#     update investment_funds
#     SET founders = '{lastDetals["response"]}'
#     WHERE fund_name = '{url["url"]["title"]}';
# """
    # print("inserted",inserted)
#     founderLinkedIn = getFounderLinkedIn(""+finalResult.get("Fund Name", "")+" company founder linkedin profile")
#     upQuery = f"""
#     update linkedin = {founderLinkedIn} where website = {finalResult.get("Website", "")}
# """
    # return {"result": data}
    
# @app.route('/dhana', methods=["GET"])
# def dhana():
#     return {"message":"Hello"}

# def get_google_maps_data(api_key, query, latitude, longitude, zoom_level=15.1):
#     location = f"@{latitude},{longitude},{zoom_level}z"
#     params = {
#         'engine': 'google_maps',
#         'q': query,
#         'type': 'search',
#         'll': location,
#         'google_domain': 'google.com',
#         'hl': 'en',
#         'api_key': api_key
#     }

#     print("Request Parameters:", params)

#     response = requests.get('https://serpapi.com/search', params=params)
#     print("Response Status Code:", response.status_code)
#     print("Response Content:", response.content)

#     if response.status_code == 200:
#         return response.json()
#     else:
#         return {"Error": response.json()}



@app.route("/update",methods=["POST"])
def update():
    url = request.get_json()
    founderLinkedIn = getFounderLinkedIn("f9b68f4d45fc1fcca74b9428af776114fae7466b74ea3ab81be7dff7ae4b4d08",url["Fund Name"]+" company founder linkedin profile")
    print(founderLinkedIn)
    upQuery = f"""
    update investment_funds
    SET linkedin = '{founderLinkedIn["link"]}'
    WHERE website = '{url["website"]}';
"""
    print(upQuery)
    updatedResult = dbCommunication(upQuery,True)
    return {"result":updatedResult}

# def parse_results(data):
#     if not data:
#         return []

#     results = data.get('local_results', [])
#     parsed_results = []

#     for place in results:
#         parsed_results.append({
#             'name': place.get('title'),
#             'address': place.get('address'),
#             'phone': place.get('phone'),
#             'rating': place.get('rating'),
#             'reviews': place.get('reviews'),
#             'price': place.get('price'),
#             'type': place.get('type'),
#             'website': place.get('website'),
#             'open_state': place.get('open_state'),
#             'hours': place.get('hours'),
#             'gps_coordinates': place.get('gps_coordinates'),
#             'thumbnail': place.get('thumbnail')
#         })

#     return parsed_results

# @app.route('/googlemap', methods=["POST"])
# def getGoogleMapData():
#     url = request.get_json()
#     api_key = 'f9b68f4d45fc1fcca74b9428af776114fae7466b74ea3ab81be7dff7ae4b4d08'
#     query = url["query"]
#     print(query)
#     latitude = 20.5937  # Approximate center of India
#     longitude = 78.9629  # Approximate center of India
#     zoom_level = 15.1
#     results = get_google_maps_data(api_key, query, latitude, longitude, zoom_level)
#     data = parse_results(results)
#     return {"result":data}


# # Define a route within the application
# @app.route('/fund-data', methods=["POST"])
# def index():
#     # Example data
#     # data = {'key': 'value'}
    
#     # Using jsonify within the context of the Flask application
#     # response = jsonify(data)
#     url = request.get_json()
#     funding_data = main(url["url"])
    
#     return funding_data

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)
