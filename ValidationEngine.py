import base64
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from QueryEngine import QueryEngine
from rdflib import RDFS
import rdflib
import urllib
from datetime import datetime
import uuid
import socket
import pandas as pd
import numpy as np
from ModelEngine import ModelEngine
import sklearn.metrics
import sklearn.calibration

fml = rdflib.Namespace("https://fairmodels.org/ontology.owl#")

class ValidationEngine:
    def __init__(self, validationEndpointUrl, dataQueryEngine, modelCacheEndpoint=None):
        self.__validationEndpoint = ValidationEndpoint(validationEndpointUrl)
        self.__dataQueryEngine = dataQueryEngine
        self.__modelCacheEndpoint = modelCacheEndpoint
    
    def processValidationRequests(self):
        print("Start processing")
        validationRequests = self.__validationEndpoint.getOpenValidationRequests()
        for validationRequestRow in validationRequests:
            print("Process request: " + validationRequestRow["id"]["value"])
            validationRequest = self.__validationEndpoint.getRequestSpecs(validationRequestRow["id"]["value"])
            validationTriples = ValidationTriples(validationRequest)
            if "query" in validationRequest:
                targetDataFrame = self.__dataQueryEngine.get_sparql_dataframe(validationRequest["query"]["value"])

                baselineCharacteristics = self.processBaselineCharacteristics(targetDataFrame)
                validationTriples.storeBaselineCharacteristics(baselineCharacteristics)

                validationMetrics = self.processModelValidation(targetDataFrame, validationRequestRow["model"]["value"])
                validationTriples.storeValidationMetrics(validationMetrics)

                validationTriples.postTriples(self.__validationEndpoint)

    def processBaselineCharacteristics(self, targetDataFrame):
        describeStats = targetDataFrame.describe(include='all')
        uniqueRows = describeStats.T[describeStats.T['unique'] == describeStats.T['count']].index.values
        describeStats[uniqueRows] = np.nan

        ##TODO: the above relies on df.describe(), which omits the unique categories.
        # Needs to be added that for every category all unique values and counts are given.

        return (targetDataFrame.shape, describeStats)
    
    def processModelValidation(self, targetDataFrame, modelUri):
        if self.__modelCacheEndpoint is not None:
            modelEngine = ModelEngine(modelUri, sparqlEndpoint=self.__modelCacheEndpoint)
        else:
            modelEngine = ModelEngine(modelUri)
        # Get ModelExecutor object for FAIR model description
        modelExecutor = modelEngine.getModelExecutor()
        targetDataFrame = modelExecutor.executeModelOnDataFrame(targetDataFrame)
        
        observedLabel = modelEngine.getModelOutputParameterName()
        outcomeData = targetDataFrame[['probability', observedLabel]].dropna()
        
        observed = outcomeData[observedLabel]
        predicted = outcomeData['probability']

        calibration_curve = None
        try:
            calibration_curve = sklearn.calibration.calibration_curve(observed, predicted)
        except:
            print("Could not calculate calibration curve (too little number of bins?)")
        
        precision, recall, prerec_thresholds = sklearn.metrics.precision_recall_curve(observed, predicted)
        fpr, tpr, roc_thresholds = sklearn.metrics.roc_curve(observed, predicted)

        metrics = {
            'count': outcomeData.shape[0],
            'auc': sklearn.metrics.roc_auc_score(observed, predicted),
            'brier': sklearn.metrics.brier_score_loss(observed, predicted),
            'precision_recall_curve': {
                'precision': precision,
                'recall': recall
            },
            'roc_curve': {
                'fpr': fpr,
                'tpr': tpr
            },
            'calibration_curve': calibration_curve
        }

        return metrics

class ValidationTriples:
    def __init__(self, requestSpecs):
        """Initialize class to generate RDF triples for given validation results"""
        self.__graph = rdflib.Graph()
        self.__resultsObject = self.__createUri("http://" + socket.getfqdn() + "/validation/" + str(uuid.uuid4()))
        self.__graph.add((self.__createUri(requestSpecs["id"]["value"]),
            fml.contains_results,
            self.__resultsObject))
        self.__graph.add((self.__resultsObject, fml.about_model, self.__createUri(requestSpecs["model"]["value"])))
        self.__graph.add(
            (
                self.__resultsObject, fml.at_time, rdflib.Literal(datetime.now())
            )
        )
        self.__graph.add(
            (
                self.__resultsObject, fml.at_location, rdflib.Literal(socket.getfqdn())
            )
        )
    
    def __createUri(self, baseUri, *subNames):
        """Create type-safe URIs given a certain base URI"""
        targetUri = str(baseUri)
        for subPath in subNames:
                targetUri = targetUri + "_" + urllib.parse.quote(subPath)

        return rdflib.term.URIRef(targetUri)

    def storeBaselineCharacteristics(self, baselineCharacteristics):
        """Loop over Pandas describe() function, and store information in RDF"""

        baselineResultsObject = self.__createUri(self.__resultsObject, "baselineResults")
        self.__graph.add((self.__resultsObject, fml.has_baseline_results, baselineResultsObject))

        shapeDataSet = baselineCharacteristics[0]
        self.__graph.add((baselineResultsObject, fml.has_row_size, rdflib.Literal(shapeDataSet[0])))
        self.__graph.add((baselineResultsObject, fml.has_column_size, rdflib.Literal(shapeDataSet[1])))

        descriptionDataSet = baselineCharacteristics[1]

        for colName in descriptionDataSet.columns:
            columnUriBaseline = self.__createUri(baselineResultsObject, colName)
            self.__graph.add((baselineResultsObject, fml.input_feature_characteristics, columnUriBaseline))
            self.__graph.add((columnUriBaseline, fml.model_parameter_name, rdflib.Literal(colName)))
            self.__graph.add((columnUriBaseline, RDFS.label, rdflib.Literal(colName + " Characteristics")))
            print(colName)

            for index, value in descriptionDataSet[colName].items():
                if not pd.isna(value):
                    columnCharacteristicUriBaseline = self.__createUri(columnUriBaseline, index)
                    self.__graph.add((columnUriBaseline, fml.has_characteristic, columnCharacteristicUriBaseline))
                    self.__graph.add((columnCharacteristicUriBaseline, fml.has_name, rdflib.Literal(index)))
                    self.__graph.add((columnCharacteristicUriBaseline, RDFS.label, rdflib.Literal(index)))
                    self.__graph.add((columnCharacteristicUriBaseline, fml.has_value, rdflib.Literal(value)))
    
    def storeValidationMetrics(self, validationMetrics):
        """Loop over validationMetrics dictionary and store information in RDF"""

        validationMetricsUri = self.__createUri(self.__resultsObject, "validationMetrics")
        self.__graph.add((self.__resultsObject, fml.has_validation_metrics, validationMetricsUri))

        self.storeValidationMetric(validationMetrics, validationMetricsUri)

    def storeValidationMetric(self, validationMetrics, baseUri):
        for key, value in validationMetrics.items():
            myMetricUri = self.__createUri(str(baseUri), key)
            self.__graph.add((baseUri, fml.has_validation_metric, myMetricUri))
            self.__graph.add((myMetricUri, fml.has_name, rdflib.Literal(key)))
            self.__graph.add((myMetricUri, RDFS.label, rdflib.Literal(key)))

            if "dict" in str(type(value)):
                self.storeValidationMetric(value, myMetricUri)
            else:
                print(key + " | " + str(type(value)))
                self.__graph.add((myMetricUri, fml.has_value, rdflib.Literal(value)))


    def retrieveTriples(self):
        """Fetch triples from in-memory graph and export as raw nt-based string of triples"""
        return self.__graph.serialize(format="nt").decode('utf-8')
    
    def postTriples(self, validationEndpoint):
        """Store triples in RDF endpoint, based on ValidationEndpoint instance given"""
        triples = self.retrieveTriples()
        validationEndpoint.storeValidationTriples(str(self.__resultsObject), triples)

class ValidationEndpoint:
    def __init__(self, endpointUrl):
        self.__endpointUrl = endpointUrl
    def __defaultQueryAssignment(self, queryString):
        sparql = SPARQLWrapper(self.__endpointUrl)
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return results["results"]["bindings"]
    def __postQuery(self, queryString):
        sparql = SPARQLWrapper(self.__endpointUrl + "/statements")
        sparql.setQuery(queryString)
        sparql.method = "POST"
        results = sparql.query()
        print(results.response.read())
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
        returnSet = self.__defaultQueryAssignment(queryString)[0]
        if "query" in returnSet:
            returnSet["query"]["value"] = self.__b64DecodeString(returnSet["query"]["value"])
        return returnSet
    def __b64EncodeString(self, message):
        message_bytes = message.encode("utf8")
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode("utf8")
        return base64_message
    def __b64DecodeString(self, base64_message):
        base64_bytes = base64_message.encode('utf8')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode("utf8")
        return message
    def storeValidationTriples(self, requestId, triplesString):
        insertQuery = """
        INSERT {
            GRAPH <%s> {
                %s
            }
        } WHERE { }
        """ % (requestId, triplesString)
        self.__postQuery(insertQuery)
    def storeQuery(self, requestId, query):
        queryDeleteString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX fml: <https://fairmodels.org/ontology.owl#>

        DELETE {
            ?id fml:has_query ?query.
        } WHERE {
            BIND(<%s> AS ?id).
            ?id fml:has_query ?query.
        }
        """ % requestId
        self.__postQuery(queryDeleteString)

        query = self.__b64EncodeString(query)
        queryString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX fml: <https://fairmodels.org/ontology.owl#>

        INSERT {
            ?id fml:has_query \"%s\".
        } WHERE {
            BIND(<%s> AS ?id).
         }
        """ % (query, requestId)
        self.__postQuery(queryString)