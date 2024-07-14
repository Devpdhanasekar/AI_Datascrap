import requests
import json

# Replace with your actual API key and endpoint
API_KEY = 'AIzaSyDBXOQTQNEMjRV47m4oH9YGcaR8vUBID5c'
API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyDBXOQTQNEMjRV47m4oH9YGcaR8vUBID5c"

# Function to get response from Gemini
def get_gemini_response():
    try:
    
        prompt_template = "Please provide detailed information on the following topic: {user_input}"

    # Example user input
        user_input = "the benefits of using AI in healthcare"
        
        data = {"contents": [{"parts": [{"text": "I converted word to html but html content does not have the style that are available in word document can you able to format the html content. In my html conent have heading paragraphs and aslo images you need format this as fit for word document."}]}]}

        # Get the response from Gemini
        # response = get_gemini_response(prompt_template, user_input)
    # print(response)
        headers = {
            'params': f'{API_KEY}',
            'Content-Type': 'application/json'
        }

        # Format the prompt with the user input
        # prompt = prompt_template.format(user_input=user_input)

        # data = {
        #     "model": "gemini-3.5-turbo",
        #     "messages": [
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": prompt}
        #     ]
        # }

        response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json()
            print("can", result)
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code}, {response.text}"
        
    except Exception as e:
        print("error", e)

# Define your prompt template

