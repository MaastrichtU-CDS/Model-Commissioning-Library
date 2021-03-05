from ModelEngine import ModelEngine

modelEngine = ModelEngine("https://fairmodels.org/models/radiotherapy/stiphout_2011.ttl")
modelExecutor = modelEngine.getModelExecutor()
modelExecutor.executeModel(inputValues={
    "https://fairmodels.org/models/radiotherapy/#InputFeature_cTStage": 3,
    "https://fairmodels.org/models/radiotherapy/#InputFeature_cNStage": 0,
    "https://fairmodels.org/models/radiotherapy/#InputFeature_TLength": 2.5
})