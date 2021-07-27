from ModelEngine import ModelEngine
from QueryEngine import QueryEngine
from ValidationEngine import ValidationEngine
import json
import pandas as pd

config = { }
with open("config.json") as f:
    config = json.load(f)

validationEngine = ValidationEngine(
    config["validation_endpoint"]["url"],
    QueryEngine(config["data_endpoint"]["url"]))
validationEngine.processValidationRequests()

# # Load ModelEngine based on FAIR description
# #modelEngine = ModelEngine("docker_test_algorithm/stiphout_docker_2011.ttl")
# modelEngine = ModelEngine("https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl", sparqlEndpoint="http://localhost:7200/repositories/model_cache")
# # Get ModelExecutor object for FAIR model description
# modelExecutor = modelEngine.getModelExecutor()

# ##########################################################
# # One execution with local values
# ##########################################################
# probability = modelExecutor.executeModel(inputValues={
#     "https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl#InputFeature_cTStage": 3,
#     "https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl#InputFeature_cNStage": 1,
#     "https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl#InputFeature_TLength": 15
# })
# print(probability)

# ##########################################################
# # One execution with ontology term
# ##########################################################
# probability = modelExecutor.executeModel(inputValues={
#     "https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl#InputFeature_cTStage": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48728",
#     "https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl#InputFeature_cNStage": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48706",
#     "https://raw.githubusercontent.com/MaastrichtU-CDS/FAIRmodels/main/models/radiotherapy/stiphout_2011.ttl#InputFeature_TLength": 15
# })
# print(probability)

# ##########################################################
# # DataFrame with local values
# ##########################################################
# inputData = pd.DataFrame(data={
#     "identifier": [1, 2, 3, 4,],
#     "cT": [3, 2, 3, 4],
#     "cN": [1, 0, 2, 1],
#     "tLength": [15, 4, 7, 10] 
# })
# print(modelExecutor.executeModelOnDataFrame(inputData))

# ##########################################################
# # DataFrame with ontology terms
# ##########################################################
# inputData = pd.DataFrame(data={
#     "identifier": [1, 2, 3, 4,],
#     "cT": [
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48728", 
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48724", 
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48728", 
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48732"
#     ],
#     "cN": [
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48706",
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48705",
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48786",
#         "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48706"
#     ],
#     "tLength": [15, 4, 7, 10] 
# })
# print(modelExecutor.executeModelOnDataFrame(inputData))

# ##########################################################
# # Query against SPARQL endpoint
# ##########################################################

# qEngine = QueryEngine("http://as-fair-01.ad.maastro.nl/repositories/sage")
# cohort = qEngine.query_from_file("testQuery.sparql")
# print(cohort)
# cohort = modelExecutor.executeModelOnDataFrame(cohort)
# print(cohort.head())

# # Check of unknown probabilities
# is_NaN = cohort.isnull()
# row_has_NaN = is_NaN.any(axis=1)
# print(cohort[row_has_NaN])