import rdflib
import os

class FML:
    prefix = "https://fairmodels.org/ontology.owl#"
    logisticRegression = prefix + "Logistic_Regression"

class ModelEngine:
    def __init__(self, modelUri):
        self.__graph = rdflib.Graph()
        self.__graph.parse(modelUri, format=rdflib.util.guess_format(modelUri))
    
    def getSparqlQueryFromFile(self, queryName):
        query = ""
        with open(os.path.join("queries", queryName + ".sparql")) as f:
            query = f.read()
        return query

    def getModelExecutor(self):
        query = self.getSparqlQueryFromFile("modelType")
        queryResults = self.__graph.query(query)
        
        for resultRow in queryResults:
            algorithmTypeString = str(resultRow["algorithmType"])

            if FML.logisticRegression == algorithmTypeString:
                return "LogReg"
        
        return None