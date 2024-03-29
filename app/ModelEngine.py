import rdflib
import os
from string import Template
import math
import docker
import requests
import pandas
from SPARQLWrapper import SPARQLWrapper, RDFXML

class FML:
    prefix = "https://fairmodels.org/ontology.owl#"
    logisticRegression = prefix + "Logistic_Regression"
    linearPredictor = prefix + "linear_predictor"
    dockerExecution = prefix + "docker_execution"

class ModelExecutor:
    def __init__(self, modelUri, modelEngine):
        self.modelEngine = modelEngine
        self.modelUri = modelUri
        self.modelParameters = None
        self.parameterValueForTermLists = None

    def executeModelOnDataFrame(self, cohortDataFrame):
        """
        Execute prediction model on a given Pandas DataFrame object. This function loops over every row in the DataFrame object, and calls the executeModel function.
        More elegant options are possible, however should be handled by classes inheriting the current ModelExecutor.
        """
        modelParameters = self.getModelParameters()

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
            try:
                myDf.at[index, "probability"] = self.executeModel(row)
            except Exception as ex:
                print(ex)
        cohortDataFrame = myDf.rename(columns=keyValue)
        return cohortDataFrame

    def executeModel(self, inputValues):
        return None

    def getModelParameters(self):
        if self.modelParameters is None:
            queryResults = self.modelEngine.performQueryFromFile("linearParams", mappings={"modelUri": self.modelUri})
            output = dict()
            for row in queryResults:
                output[str(row["inputFeature"])] = {
                    "featureName": str(row["inputFeatureName"]),
                    "beta": row["beta"]
                }
                if row["beta"] is not None:
                    output[str(row["inputFeature"])]["beta"] = float(str(row["beta"]))
            self.modelParameters = output
        return self.modelParameters
    def replaceParameterToLocalValue(self, parameterId, inputValue):
        paramMapping = self.getValueForTermList(parameterId)
        if paramMapping is not None:
            if inputValue in paramMapping:
                inputValue = paramMapping[inputValue]
        return inputValue
    def getValueForTermList(self, modelParameter):
        ## does a lookup on the translation values for a given model parameter
        if self.parameterValueForTermLists is None:
            self.parameterValueForTermLists = {}
            queryResults = self.modelEngine.performQueryFromFile("valueForTermList", mappings={"modelParameter": modelParameter})
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
                if inputFeatureName not in self.parameterValueForTermLists:
                    self.parameterValueForTermLists[inputFeatureName] = {}
                self.parameterValueForTermLists[inputFeatureName][termName] = termValue
        
        if modelParameter in self.parameterValueForTermLists:
            return self.parameterValueForTermLists[modelParameter]
        else:
            return None

class DockerExecutor(ModelExecutor):
    """
    This class handles the execution of docker containers, as specified in the FairModels.org ontology.
    At instance creation, the docker container will be started (and bound to localhost). At teardown, the container will be stopped and removed.
    The main function for invocation is executeModel.
    """

    def __init__(self, modelUri, modelEngine):
        super().__init__(modelUri, modelEngine)
        self.__client = docker.from_env()
        self.__fetchDockerParams()
        try:
            self.__client.images.pull(self.__dockerParams["imageUrl"])
        except:
            print("Could not fetch image " + self.__dockerParams["imageUrl"])
        self.__algorithmContainer = self.__client.containers.run(self.__dockerParams["imageUrl"], detach=True, ports={self.__dockerParams["containerPort"] + '/tcp': ('127.0.0.1', 5000)})

    def __fetchDockerParams(self):
        queryResults = self.modelEngine.performQueryFromFile("dockerParams", mappings={"modelUri": self.modelUri})
        for row in queryResults:
            self.__dockerParams = {
                "imageUrl": row["imageUrl"],
                "containerPort": row["containerPort"],
                "invocationUrl": row["invocationUrl"],
                "invocationUrlBulk": row["invocationUrlBulk"],
                "httpMethod": row["httpMethod"],
                "acceptType": row["acceptType"]
            }
            break
    
    def executeModel(self, inputValues):
        """
        Execute the prediction model given the dictionary of input values.
        Return value: Probability (float) or None when execution failed
        """
        modelParameters = self.getModelParameters()
        if inputValues is not None:
            try:
                for parameterId in modelParameters:
                    if parameterId in inputValues:
                        inputValue = self.replaceParameterToLocalValue(parameterId, inputValues[parameterId])
                        inputValues[parameterId] = inputValue
                    elif modelParameters[parameterId]["featureName"] in inputValues:
                        inputValue = self.replaceParameterToLocalValue(parameterId, inputValues[modelParameters[parameterId]["featureName"]])
                        inputValues[parameterId] = inputValue

                modelUrl = "http://localhost:5000" + self.__dockerParams["invocationUrl"]
                requestFunction = None
                if self.__dockerParams["httpMethod"].upper() == "POST":
                    requestFunction = requests.post
                else:
                    print("Only HTTP POST is currently supported in this client engine.")
                    return None
                
                response = requestFunction(modelUrl, json=inputValues).json()
                if "probability" in response:
                    return response["probability"]
            except Exception as error:
                print("Could not execute model: " + str(error))
            return None
    
    def executeModelOnDataFrame(self, cohortDataFrame):
        """
        Execute prediction model on a given Pandas DataFrame object. This function loops over every row in the DataFrame object, and calls the executeModel function.
        More elegant options are possible, however should be handled by classes inheriting the current ModelExecutor.
        """
        modelParameters = self.getModelParameters()

        reverseIndex = {}
        keyValue = {}
        for key in modelParameters:
            parameter = modelParameters[key]

            if parameter["featureName"] not in cohortDataFrame.columns:
                raise NameError("Could not find column %s" % parameter["featureName"])
            reverseIndex[parameter["featureName"]] = key
            keyValue[key] = parameter["featureName"]

        cohortDataFrame = cohortDataFrame.rename(columns=reverseIndex)
        for key in modelParameters:
            paramMapping = self.getValueForTermList(key)
            if paramMapping is not None:
                for paramKey in paramMapping:
                    cohortDataFrame[key] = cohortDataFrame[key].replace(paramKey, paramMapping[paramKey])
        cohortDataFrame["probability"] = None

        modelUrl = "http://localhost:5000" + self.__dockerParams["invocationUrlBulk"]
        requestFunction = None
        if self.__dockerParams["httpMethod"].upper() == "POST":
            requestFunction = requests.post
        else:
            print("Only HTTP POST is currently supported in this client engine.")
            return None

        response = requestFunction(modelUrl, json=cohortDataFrame.to_json()).json()
        cohortDataFrame = pandas.read_json(response)
        
        cohortDataFrame = cohortDataFrame.rename(columns=keyValue)
        return cohortDataFrame

    def __del__(self):
        print("Stopping container")
        self.__algorithmContainer.stop()
        self.__algorithmContainer.remove()

class LogisticRegression(ModelExecutor):        
    def executeModel(self, inputValues):
        modelParameters = self.getModelParameters()
        if inputValues is not None:
            intercept = self.__getInterceptParameter()
            weightedSum = self.__calculateWeightedSum(modelParameters, inputValues)
            lp = intercept + weightedSum
            probability = 1 / (1 + math.exp(-1 * lp))
            return probability
    def __calculateWeightedSum(self, modelParameters, inputValues):
        lp = float(0)
        for parameterId in modelParameters:
            inputValue = self.replaceParameterToLocalValue(parameterId, inputValues[parameterId])
            parameter = modelParameters[parameterId]
            weightedVar = parameter["beta"] * inputValue
            lp = lp + weightedVar
        return lp
    def __getInterceptParameter(self):
        queryResults = self.modelEngine.performQueryFromFile("intercept", mappings={"modelUri": self.modelUri})
        for row in queryResults:
            return float(str(row["intercept"]))

class ModelEngine:
    """
    Base class to fetch model specifications, and select the execution type of the model.
    """
    def __init__(self, modelUri, sparqlEndpoint=None, libraryLocation=None):
        self.__graph = rdflib.Graph()
        self.__libraryLocation = libraryLocation
        self.__modelUri = modelUri
        if sparqlEndpoint is None:
            self.__graph.parse(modelUri, format=rdflib.util.guess_format(modelUri))
        else:
            rdfXmlDataString = self.__getFromEndpoint(modelUri, sparqlEndpoint)
            self.__graph.parse(data=rdfXmlDataString, format='xml')
    def __getFromEndpoint(self, modelUri, sparqlEndpoint):
        sparql = SPARQLWrapper(sparqlEndpoint)

        sparql.setQuery("""
            CONSTRUCT {
                ?s ?p ?o.
            } WHERE {
                GRAPH <%s> {
                    ?s ?p ?o.
                }
            }
        """ % modelUri)

        sparql.setReturnFormat(RDFXML)
        results = sparql.query().convert()
        return results.serialize(format='xml')
    def __getSparqlQueryFromFile(self, queryName, mappings=None):
        query = ""
        if self.__libraryLocation is not None:
            pathForQuery = os.path.join(self.__libraryLocation, "queries", queryName + ".sparql")
        else:
            pathForQuery = os.path.join("queries", queryName + ".sparql")
        with open(pathForQuery) as f:
            query = f.read()
        if mappings is not None:
            temp_obj = Template(query)
            query = temp_obj.substitute(**mappings)
        return query

    def performQueryFromFile(self, queryName, mappings=None):
        query = self.__getSparqlQueryFromFile(queryName=queryName, mappings=mappings)
        return self.__graph.query(query)
    
    def getModelExecutor(self):
        """
        Determines the ModelExecutor subclass, based on algorithm and execution type.
        Return value: Instance of ModelExecutor, based on the execution type. If no supported type is found, None will be returned.
        """
        queryResults = self.performQueryFromFile("modelType")
        
        for resultRow in queryResults:
            algorithmTypeString = str(resultRow["algorithmType"])
            algorithmExecutionTypeString = str(resultRow["algorithmExecutionType"])

            if FML.logisticRegression == algorithmTypeString:
                if FML.linearPredictor == algorithmExecutionTypeString:
                    return LogisticRegression(str(resultRow["algorithm"]), self)
            
            if FML.dockerExecution == algorithmExecutionTypeString:
                print("Unknown algorithm type, but it is definately a docker-based execution")
                return DockerExecutor(str(resultRow["algorithm"]), self)
        
        return None
    
    def getModelOutputParameterName(self):
        mappings = {
            "modelUri": self.__modelUri
        }
        queryResults = self.performQueryFromFile("outputParameter", mappings=mappings)
        for resultRow in queryResults:
            print(resultRow)
            return str(resultRow["outputParameter"])
        return None
