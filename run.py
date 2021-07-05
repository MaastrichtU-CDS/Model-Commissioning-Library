from flask import Flask, render_template, request
from SPARQLWrapper import SPARQLWrapper, JSON
import json

with open("config.json") as f:
    config = json.load(f)

app = Flask(__name__)

class ValidationEndpoint:
    def __init__(self, endpointUrl):
        self.__endpointUrl = endpointUrl
    def __defaultQueryAssignment(self, queryString):
        sparql = SPARQLWrapper(self.__endpointUrl)
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return results["results"]["bindings"]
    def getOpenValidationRequests(self):
        queryString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX fml: <https://fairmodels.org/ontology.owl#>

        SELECT ?id ?dateTime ?model ?query
        WHERE {
            ?id rdf:type fml:ValidationRequest.
            ?id fml:has_status [ rdf:type fml:Requested ].
            ?id fml:at_time ?dateTime.
            ?id fml:about_model ?model.
        }
        """
        return self.__defaultQueryAssignment(queryString)
    def getRequestSpecs(self, requestId):
        queryString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX fml: <https://fairmodels.org/ontology.owl#>

        SELECT ?id ?dateTime ?model ?query
        WHERE {
            BIND(<%s> AS ?id).
            ?id rdf:type fml:ValidationRequest.
            ?id fml:has_status [ rdf:type fml:Requested ].
            ?id fml:at_time ?dateTime.
            ?id fml:about_model ?model.
            OPTIONAL { ?id fml:has_query ?query }.
        }
        """ % requestId
        print(queryString)
        return self.__defaultQueryAssignment(queryString)[0]
class ModelEndpoint:
    def __init__(self, endpointUrl):
        self.__endpointUrl = endpointUrl
        self.__sparql = SPARQLWrapper(self.__endpointUrl)
    def getModelInputParameters(self, modelUri):
        queryString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX fml: <https://fairmodels.org/ontology.owl#>

        SELECT ?informationElement ?informationElementType ?informationElementTypeLabel ?inputFeature ?local_param_name ?input_feature_category WHERE {
            BIND (<%s> AS ?model).
            ?model fml:needs_information_element ?informationElement.
            ?informationElement rdf:type ?informationElementType.
            FILTER(?informationElementType NOT IN (fml:InformationElement)).
            ?informationElementType rdfs:label ?informationElementTypeLabel.
            
            ?inputFeature fml:based_on_information_element ?informationElement;
                rdf:type fml:Algorithm_Input_Parameter;
                fml:model_parameter_name ?local_param_name;
                fml:is_variable_type [ rdf:type ?input_feature_category ].
        }
        """ % modelUri
        self.__sparql.setQuery(queryString)
        self.__sparql.setReturnFormat(JSON)
        results = self.__sparql.query().convert()
        return results["results"]["bindings"]

validationEndpoint = ValidationEndpoint(config["validation_endpoint"]["url"])
modelEndpoint = ModelEndpoint(config["model_cache_endpoint"]["url"])

@app.route('/')
def index():
    requestUri = request.args.get("requestUri")
    
    if requestUri is not None:
        requestSpecs = validationEndpoint.getRequestSpecs(requestUri)
        modelParamsList = modelEndpoint.getModelInputParameters(requestSpecs["model"]["value"])
        return render_template('editQuery.html',
            requestSpecs=requestSpecs,
            modelParamsList=modelParamsList)

    return render_template('index.html', vRequests=validationEndpoint.getOpenValidationRequests())

if (__name__ == "__main__"):
    app.run(host="0.0.0.0", port=5000, debug=True)