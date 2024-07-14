from flask import Flask, request, jsonify

from flask_cors import CORS
from gemini_connect import get_gemini_response
app = Flask(__name__)
CORS(app)
@app.route("/scrap", methods=["GET"])

def getDriver():
    try:
        # data = request.json
        response = get_gemini_response()
        return {"Message":response, "status":200},200
        
    except Exception as e:
        return {"Message": "something went wrong", "status":400},400
    
if(__name__ == "__main__"):
    app.run()
    

