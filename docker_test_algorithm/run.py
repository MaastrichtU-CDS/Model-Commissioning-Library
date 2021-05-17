from flask import Flask, Response, request
import json
import signal
import math
import sys

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
    
    cT_value = int(data["cT"])
    cN_value = int(data["cN"])
    tLength_value = int(data["tLength"])
    
    intercept = float("-0.60")
    cT_beta = float("-0.074")
    cN_beta = float("-0.060")
    tLength_beta = float("-0.085")

    linearPredictor = intercept + (cT_value * cT_beta) + (cN_value * cN_beta) + (tLength_value * tLength_beta)
    probability = 1 / (1 + math.exp(-1 * linearPredictor))
    return json.dumps({"success": True, "probability": probability})

app.run(debug=True, host='0.0.0.0', port=5000)