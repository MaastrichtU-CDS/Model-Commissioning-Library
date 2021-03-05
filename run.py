from ModelEngine import ModelEngine

modelEngine = ModelEngine("https://fairmodels.org/models/radiotherapy/stiphout_2011.ttl")
modelExecutor = modelEngine.getModelExecutor()
modelExecutor.executeModel()