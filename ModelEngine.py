import rdflib
import os
from string import Template
import math

class FML:
    prefix = "https://fairmodels.org/ontology.owl#"
    logisticRegression = prefix + "Logistic_Regression"

class LogisticRegression:
    def __init__(self, modelUri, modelEngine):
        self.__modelEngine = modelEngine
        self.__modelUri = modelUri
        self.__modelParameters = None
        self.__parameterValueForTermLists = None
    def executeModelOnDataFrame(self, cohortDataFrame):
        modelParameters = self.__getModelParameters()

        reverseIndex = {}
        keyValue = {}
        for key in modelParameters:
            parameter = modelParameters[key]

            if parameter["featureName"] not in cohortDataFrame.columns:
                raise NameError("Could not find column %s" % parameter["featureName"])
            reverseIndex[parameter["featureName"]] = key
            keyValue[key] = parameter["featureName"]

        myDf = cohortDataFrame.rename(columns=reverseIndex)
        myDf["probability"] = None

        for index, row in myDf.iterrows():
            # convert short column name to long version
            myDf.at[index, "probability"] = self.executeModel(row)
        
        cohortDataFrame = myDf.rename(columns=keyValue)
        return cohortDataFrame
    def executeModel(self, inputValues):
        modelParameters = self.__getModelParameters()
        if inputValues is not None:
            intercept = self.__getInterceptParameter()
            weightedSum = self.__calculateWeightedSum(modelParameters, inputValues)
            lp = intercept + weightedSum
            probability = 1 / (1 + math.exp(-1 * lp))
            return probability
    def __calculateWeightedSum(self, modelParameters, inputValues):
        lp = float(0)
        for parameterId in modelParameters:
            parameter = modelParameters[parameterId]
            weightedVar = parameter["beta"] * inputValues[parameterId]
            lp = lp + weightedVar
        return lp
    def __replaceParameterToLocalValue(self, parameterId, inputValue):
        paramMapping = self.__getValueForTermList(parameterId)
        if paramMapping is not None:
            if inputValue in paramMapping:
                inputValue = paramMapping[inputValue]
        return inputValue
    def __getModelParameters(self):
        if self.__modelParameters is None:
            queryResults = self.__modelEngine.performQueryFromFile("linearParams", mappings={"modelUri": self.__modelUri})
            output = dict()
            for row in queryResults:
                output[str(row["inputFeature"])] = {
                    "featureName": str(row["inputFeatureName"]),
                    "beta": float(str(row["beta"]))
                }
            self.__modelParameters = output
        return self.__modelParameters
    def __getValueForTermList(self, modelParameter):
        ## does a lookup on the translation values for a given model parameter
        if self.__parameterValueForTermLists is None:
            self.__parameterValueForTermLists = {}
            queryResults = self.__modelEngine.performQueryFromFile("valueForTermList", mappings={"modelParameter": modelParameter})
            for row in queryResults:
                inputFeatureName = str(row["inputFeature"])
                termName = str(row["term"])
                termValue = row["value"]

                # Replace termValue types
                termValueNew = str(termValue)
                termValueType = str(termValue.datatype)
                if termValueType=="http://www.w3.org/2001/XMLSchema#int":
                    termValueNew = int(str(termValue))
                if termValueType=="http://www.w3.org/2001/XMLSchema#integer":
                    termValueNew = int(str(termValue))
                if termValueType=="http://www.w3.org/2001/XMLSchema#double":
                    termValueNew = float(str(termValue))
                termValue = termValueNew

                # insert termValues in list
                if inputFeatureName not in self.__parameterValueForTermLists:
                    self.__parameterValueForTermLists[inputFeatureName] = {}
                self.__parameterValueForTermLists[inputFeatureName][termName] = termValue
        
        if modelParameter in self.__parameterValueForTermLists:
            return self.__parameterValueForTermLists[modelParameter]
        else:
            return None
    def __getInterceptParameter(self):
        queryResults = self.__modelEngine.performQueryFromFile("intercept", mappings={"modelUri": self.__modelUri})
        for row in queryResults:
            return float(str(row["intercept"]))

class ModelEngine:
    def __init__(self, modelUri):
        self.__graph = rdflib.Graph()
        self.__graph.parse(modelUri, format=rdflib.util.guess_format(modelUri))
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