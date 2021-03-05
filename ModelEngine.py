import rdflib
import os
from string import Template

class FML:
    prefix = "https://fairmodels.org/ontology.owl#"
    logisticRegression = prefix + "Logistic_Regression"

class LogisticRegression:
    def __init__(self, modelUri, modelEngine):
        self.__modelEngine = modelEngine
        self.__modelUri = modelUri
    def executeModel(self, inputValues=None):
        modelParameters = self.getModelParameters()
        if inputValues is not None:
            lp = self.calculateLinearPredictor(modelParameters, inputValues)
            print(lp)
    def calculateLinearPredictor(self, modelParameters, inputValues):
        lp = float(0)
        for parameterId in modelParameters:
            parameter = modelParameters[parameterId]
            weightedVar = parameter["beta"] * inputValues[parameterId]
            lp = lp + weightedVar
        return lp
    def getModelParameters(self):
        queryResults = self.__modelEngine.performQueryFromFile("linearParams", mappings={"modelUri": self.__modelUri})
        output = dict()
        for row in queryResults:
            output[str(row["inputFeature"])] = {
                "featureName": str(row["inputFeatureName"]),
                "beta": float(str(row["beta"]))
            }
        return output

class ModelEngine:
    def __init__(self, modelUri):
        self.__graph = rdflib.Graph()
        self.__graph.parse(modelUri, format=rdflib.util.guess_format(modelUri))
    def test(self):
        print("hi there!")
    def __getSparqlQueryFromFile(self, queryName, mappings=None):
        query = ""
        with open(os.path.join("queries", queryName + ".sparql")) as f:
            query = f.read()
        if mappings is not None:
            temp_obj = Template(query)
            query = temp_obj.substitute(**mappings)
        return query

    def performQueryFromFile(self, queryName, mappings=None):
        query = self.__getSparqlQueryFromFile(queryName=queryName, mappings=mappings)
        return self.__graph.query(query)
    
    def getModelExecutor(self):
        queryResults = self.performQueryFromFile("modelType")
        
        for resultRow in queryResults:
            algorithmTypeString = str(resultRow["algorithmType"])

            if FML.logisticRegression == algorithmTypeString:
                return LogisticRegression(str(resultRow["algorithm"]), self)
        
        return None