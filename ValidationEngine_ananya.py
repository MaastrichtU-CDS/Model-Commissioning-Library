"""
Validation class for validating models. Added Concordance index validation method
"""

class ValidationEngine:
    def __init__(self, modelUri, validationMethod, inputVariables):
        self.validationEngine = modelEngine
        self.validationMethod = validationMethod
        self.inputVariables = inputVariables
        self.modelUri = modelUri
        self.modelParameters = None
        self.parameterValueForTermLists = None
    
    def getData():
        # sparql query to get data in dataframe 
        
    def concordanceIndex(modelUri, data,inputVariables):
        if 'overlijden' and 'Datum_overlijden' in inputVariables:
            n_total_correct = 0
            n_total_comparable = 0
            dfSort = data.sort_values(by=['Datum_overlijden'])
            dfLoc = data.loc[df['overlijden'] == 0]
            for row in data[data['overlijden'] == 1].itertuples():
                comparable_rows = df2.loc[(df2['Datum_overlijden'] > row.end_time), 'lp'].values
                n_correct_rows = (comparable_rows < row.lp).sum()
                n_total_correct += n_correct_rows
                n_total_comparable += len(comparable_rows)
            
            cindex = n_total_correct / n_total_comparable if n_total_comparable else N
            
            return cindex    
    
    def validator(self, modelUri,validationMethod,inputVariables):
        data = self.getData()
        if validationMethod = "Harreld's Concordance Index":
            try:
                cindex = concordanceIndex(modelUri,data,inputVariables)
            except:
                return ("An exception occured")
    