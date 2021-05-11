from ModelEngine import ModelEngine
import pandas as pd

modelEngine = ModelEngine("https://fairmodels.org/models/radiotherapy/stiphout_2011.ttl")
modelExecutor = modelEngine.getModelExecutor()
probability = modelExecutor.executeModel(inputValues={
    "https://fairmodels.org/models/radiotherapy/#InputFeature_cTStage": 3,
    "https://fairmodels.org/models/radiotherapy/#InputFeature_cNStage": 1,
    "https://fairmodels.org/models/radiotherapy/#InputFeature_TLength": 15
})
print(probability)

probability = modelExecutor.executeModel(inputValues={
    "https://fairmodels.org/models/radiotherapy/#InputFeature_cTStage": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48728",
    "https://fairmodels.org/models/radiotherapy/#InputFeature_cNStage": 1,
    "https://fairmodels.org/models/radiotherapy/#InputFeature_TLength": 15
})
print(probability)

inputData = pd.DataFrame(data={
    "identifier": [1, 2, 3, 4,],
    "cT": [3, 2, 3, 4],
    "cN": [1, 0, 2, 1],
    "tLength": [15, 4, 7, 10] 
})
print(modelExecutor.executeModelOnDataFrame(inputData))

inputData = pd.DataFrame(data={
    "identifier": [1, 2, 3, 4,],
    "cT": [
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48728", 
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48724", 
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48728", 
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48732"
    ],
    "cN": [
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48706",
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48705",
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48786",
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#C48706"
    ],
    "tLength": [15, 4, 7, 10] 
})
print(modelExecutor.executeModelOnDataFrame(inputData))