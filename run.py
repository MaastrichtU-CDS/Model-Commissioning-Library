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

inputData = pd.DataFrame(data={
    "identifier": [1, 2, 3, 4, 5],
    "cT": [3, 2, 3, 4],
    "cN": [1, 0, 2, 1],
    "tLength": [15, 4, 7, 10] 
})