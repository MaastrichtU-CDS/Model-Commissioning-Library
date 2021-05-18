from flask import Flask, Response, request
import json
import signal
import math
import sys
import pandas as pd

app = Flask('TaskMaster')

def signal_handler(sig, frame):
    print("closing application")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


@app.route('/', methods=["GET"])
def index():
    return "Hello, World"

@app.route('/', methods=["POST"])
def calculate_single():
    try:
        data = request.get_json()
    except:
        return Response(json.dumps({"success": False, 'message': "Could not parse input as JSON"}), mimetype="application/json")
    
    probability = calculate(data)
    
    return json.dumps({"success": True, "probability": probability})

def calculate(data):
    cT_value = int(data["https://fairmodels.org/models/radiotherapy/#InputFeature_cTStage"])
    cN_value = int(data["https://fairmodels.org/models/radiotherapy/#InputFeature_cNStage"])
    tLength_value = int(data["https://fairmodels.org/models/radiotherapy/#InputFeature_TLength"])
    
    intercept = float("-0.60")
    cT_beta = float("-0.074")
    cN_beta = float("-0.060")
    tLength_beta = float("-0.085")

    linearPredictor = intercept + (cT_value * cT_beta) + (cN_value * cN_beta) + (tLength_value * tLength_beta)
    probability = 1 / (1 + math.exp(-1 * linearPredictor))
    return probability

@app.route('/bulk', methods=["POST"])
def calculate_bulk():
    try:
        data = request.get_json()
    except:
        return Response(json.dumps({"success": False, 'message': "Could not parse input as JSON"}), mimetype="application/json")
    
    myDf = pd.read_json(data)
    for index, row in myDf.iterrows():
            # convert short column name to long version
            try:
                myDf.at[index, "probability"] = calculate(row)
            except Exception as ex:
                print(ex)
    return json.dumps(myDf.to_json())

app.run(debug=True, host='0.0.0.0', port=5000)