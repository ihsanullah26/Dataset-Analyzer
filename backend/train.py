from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import numpy as np
from sdv.metadata import SingleTableMetadata
from sdv.single_table import GaussianCopulaSynthesizer, CTGANSynthesizer, TVAESynthesizer
from sdv.sampling import Condition
from sdv.evaluation.single_table import evaluate_quality
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
from sdv.evaluation.single_table import evaluate_quality
from fastapi.responses import JSONResponse

app = FastAPI()

# Allow React to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)


#function to Smotth the outlier using conditional sampling of SDV
def SmoothOutliers(dataset,synthesizer):
    y = dataset.columns[-1]
    Q1 = dataset[y].quantile(0.25)
    Q3 = dataset[y].quantile(0.75)
    IQR = Q3 - Q1
    Left_bound = Q1 - (1.5 * IQR)
    Right_bound = Q3 + (1.5 * IQR)

    #find indices of the outliers
    outlier_indices = dataset[(dataset[y] < Left_bound) | (dataset[y] > Right_bound)].index
    
    #if no outliers
    if(len(outlier_indices) == 0):
        return dataset
    else:
        for idx in outlier_indices:
            row_context = dataset.loc[idx].drop(y).to_dict()
            condition = Condition(num_rows = 1,column_values = row_context)
            try:
                refined_sample = synthesizer.sample_from_conditions(conditions=[condition])
                dataset.at[idx,y] = refined_sample[y].iloc[0]
            except:
                continue
    
    return dataset

#function to fixed The Skewness of the data 
def FixedSkewness(dataset,synthesizer):
    y = dataset.columns[-1]
    skew_val = dataset[y].skew()

    if abs(skew_val) > 0.65:
        total_rows = len(dataset)
        goal_count = int(total_rows * 0.25)

        #Determine direction
        if skew_val > 0:
            percentile = 0.90 if skew_val >1.2 else 0.80
            threshold = dataset[y].quantile(percentile)
            curren_tail_count = len(dataset[dataset[y] >=threshold])
            #use SDV conditions
            val_range = (threshold,dataset[y].max())
        else:
            percentile = 0.10 if skew_val <-1.2 else 0.20
            threshold = dataset[y].quantile(percentile)
            curren_tail_count = len(dataset[dataset[y] <=threshold])
            #use SDV conditions
            val_range = (dataset[y].min(),threshold)
        
        rows_to_add = max(0,goal_count - curren_tail_count)
        if rows_to_add > 0:
            condition = Condition(num_rows = rows_to_add,column_values= {y:val_range})
            try:
                Extra_data = synthesizer.sample_from_conditions(conditions=[condition])
                dataset = pd.concat([dataset,Extra_data],ignore_index=True)
            except Exception as e:
                print(f"Skeweness Fixed Skipped {e}\n")
    return dataset

################################################################################
#function to decide which of SDV model to use to generate synthetic data 

def get_routing_info(df, target_col):
    # Calculate the percentage of each group (Normalize=True Means give me ratio instead of numbers)
    counts = df[target_col].value_counts(normalize=True)
    minority_ratio = counts.min()
    
    # Route based on your logic: Mild (>30%), Moderate (>10%), Severe (<10%)
    if minority_ratio > 0.30 and minority_ratio <0.45:
        return "mild", GaussianCopulaSynthesizer
    elif minority_ratio > 0.10:
        return "moderate", CTGANSynthesizer
    else:
        return "severe", TVAESynthesizer

#function to clear the boundary so it is easy for a model to predict a class
def clean_boundary_overlap(df, target_col):
    cleaned_parts = []
    for label in df[target_col].unique():
        class_subset = df[df[target_col] == label]
        num_cols = class_subset.select_dtypes(include=[np.number]).columns
        
        if not num_cols.empty:
            # Calculate how far each point is from the average (Z-score)
            z_scores = np.abs((class_subset[num_cols] - class_subset[num_cols].mean()) / class_subset[num_cols].std())
            # Keep rows that are within 2 standard deviations (the "Typical" rows)
            #z_scores < 2.0: In statistics, about 95% of "normal" 
            # data falls within 2.0 standard deviations. Anything higher 
            # than 2.0 is considered an outlier or extreme noise.
            filtered = class_subset[(z_scores < 2.0).all(axis=1)]
            cleaned_parts.append(filtered)
        else:
            cleaned_parts.append(class_subset)
            
    return pd.concat(cleaned_parts, ignore_index=True)

def run_synthetic_repair_pipeline(df):
    # Limit generation to 10 times the original minority size
    #EXample:
    # 1. We count the minority group
    # Suppose Minority = 10 rows    
    # Suppose Majority = 1,000 rows
    # 2. Shortfall is the "Ideal World" goal
    #shortfall = 1000 - 10  # Result: 990 rows needed to be equal
    # 3. Max Allowed is the "Safety Guardrail" (10x rule)
    #max_allowed = 10 * 10  # Result: 100 rows
    # 4. The Decision Line
    #to_generate = min(990, 100) # Result: 100
    # 1. Initialize Metadata
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)
    target_col = df.columns[-1]
    
    # 2. Get the right Model for the job
    severity, ModelClass = get_routing_info(df, target_col)
    print(f"Severity: {severity}. Using: {ModelClass.__name__}")
    
    # 3. Train the Model
    synthesizer = ModelClass(metadata)
    synthesizer.fit(df)
    
    # 4. Calculate Shortfall with 10x Guardrail
    counts = df[target_col].value_counts()
    minority_val = counts.idxmin()
    shortfall = counts.max() - counts.min()
    
    # --- FIX STARTS HERE ---
    if shortfall <= 0:
        print("Dataset is already balanced. Skipping oversampling.")
        report = evaluate_quality(df, df, metadata)
        return df, report.get_score()
    # --- FIX ENDS HERE ---

    max_allowed = counts.min() * 10
    to_generate = int(min(shortfall, max_allowed)) # Ensure it's an int
    
    # Second safety check: SDV needs at least 1 row
    if to_generate > 0:
        print(f"Generating {to_generate} rows for minority class: {minority_val}")
        condition = Condition(num_rows=to_generate, column_values={target_col: minority_val})
        synthetic_rows = synthesizer.sample_from_conditions(conditions=[condition])
        
        # 6. Combine and Clean Overlap
        combined_df = pd.concat([df, synthetic_rows], ignore_index=True)
        final_df = clean_boundary_overlap(combined_df, target_col)
    else:
        final_df = df

    # 7. Final Quality Check
    report = evaluate_quality(df, final_df, metadata)
    score = report.get_score()
    
    return final_df, score

@app.post('/analyze_and_fill_gap')
async def Analyze_and_fill_gaps(
    file: UploadFile = File(...),
    modelType: str = Form(...),
):
    try:
        contents = await file.read()
        dataframe = pd.read_csv(io.BytesIO(contents))
        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(dataframe)

        # Initialize score to handle the Regression case
        score = None 

        # train a base model (Using mode/median for NaNs)
        train_df = dataframe.copy()
        for col in train_df.columns:
            if train_df[col].dtype in ['int64', 'float64']:
                train_df[col] = train_df[col].fillna(train_df[col].median())
            else:
                train_df[col] = train_df[col].fillna(train_df[col].mode()[0] if not train_df[col].mode().empty else "Unknown")

        synthesizer_a = GaussianCopulaSynthesizer(metadata)
        synthesizer_a.fit(train_df)

        if modelType == "Regression":
            # 1. Smooth Outliers
            dataframe = SmoothOutliers(dataframe, synthesizer_a)
            # 2. Fix Skewness (Over-sample the tails)
            dataframe = FixedSkewness(dataframe, synthesizer_a)
        
        elif modelType == "Classification":
            # 1. Re-balance classes (Minority Over-sampling)
            dataframe, score = run_synthetic_repair_pipeline(dataframe)

        # Final string conversion for header
        final_score = str(score) if score is not None else "N/A"

        # 1. Create the CSV data in memory
        stream = io.StringIO()
        dataframe.to_csv(stream, index=False)
        
        # 2. Move to a BytesIO stream for the response
        response_stream = io.BytesIO(stream.getvalue().encode())
        
        return StreamingResponse(
            response_stream,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=updated_dataset.csv",
                "X-Quality-Score": final_score,
                "Access-Control-Expose-Headers": "X-Quality-Score" 
            }
        )
       
    except Exception as e:
        # Logging the actual error helps in debugging
        print(f"API Error: {str(e)}") 
        raise HTTPException(status_code=400, detail=f"Processing Error: {str(e)}")


@app.post("/train")
async def train_Model(
    file : UploadFile = File(...),
    modelType: str = Form(...),
    modelName : str = Form(...)
):
  
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        if (modelType == "Regression"):
            # Train your regression model here using df
            if(modelName == "Linear"):
                model = LinearRegression()
            elif (modelName == "DecisionTree"):
                model = DecisionTreeRegressor()  # Train Decision Tree Regressor
            elif (modelName == "RandomForest"):
                model = RandomForestRegressor()  # Train Random Forest Regressor
        elif(modelType == "Classification"):
            # Train your classification model here using df
            if(modelName == "Linear"):
                model = LogisticRegression()  # Train Logistic Regression
            elif (modelName == "DecisionTree"):
                model = DecisionTreeClassifier()  # Train Decision Tree Classifier
            elif (modelName == "RandomForest"):
                model = RandomForestClassifier()  # Train Random Forest Classifier

#now     separate features and target variable,assuming the last column is the target variable
        X = df.iloc[:,:-1]  # Features
        y = df.iloc[:,-1]   # Target variable

        # 2. GENERALIZED VALIDATION
        # Check if the target is categorical (strings) or has very few unique values
        is_categorical = y.dtype == 'object' or y.nunique() < 10
        actual_task = "Classification" if is_categorical else "Regression"

        # 3. If user selected the wrong type, stop and inform them
        if modelType != actual_task:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "MISMATCH",
                    "actual_task": actual_task,
                    "message": f"Dataset detected as {actual_task}. Please switch from {modelType}."
                }
            )
        #now train test and split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        predictons = model.predict(X_test)

        #now finding different metrics which will be shown to the user
        if modelType == "Regression":
            mse = mean_squared_error(y_test, predictons)
            r2 = r2_score(y_test, predictons)
        else:
            accuracy = accuracy_score(y_test, predictons)
            report = classification_report(y_test, predictons)

        return{
            "message": "Model trained successfully",
            "metrics": {
                "mse": mse if modelType == "Regression" else None,
                "r2": r2 if modelType == "Regression" else None,
                "accuracy": accuracy if modelType == "Classification" else None,
                "classification_report": report if modelType == "Classification" else None
            }
        }

    except HTTPException as e:
        raise e # Re-raise the mismatch exception so React sees it
    except Exception as e:
        print(f"Error {e} Occurred")
        raise HTTPException(status_code=500, detail={"type": "SERVER_ERROR", "message": str(e)})


#function to select synthesizer Types based on User input
def ChooseSynthesizer(synthesizer):
    if synthesizer == "Guassian":
        return GaussianCopulaSynthesizer
    elif synthesizer == "CTGAN":
        return CTGANSynthesizer
    else:
        return TVAESynthesizer

@app.post("/GenerateRandomData")
async def GenerateRandomData(
    file: UploadFile = File(...),
    Synthesizer: str = Form(...),
    Num_of_rows: int = Form(...)
):
    try:
        content = await file.read()
        dataset = pd.read_csv(io.BytesIO(content))

        syn = ChooseSynthesizer(Synthesizer)

        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(dataset)

        synthesizer = syn(metadata)
        synthesizer.fit(dataset)

        synthetic_data = synthesizer.sample(num_rows=Num_of_rows)

        # ✅ Quality report
        quality_report = evaluate_quality(
            real_data=dataset,
            synthetic_data=synthetic_data,
            metadata=metadata
        )

        return JSONResponse(content={
            "synthetic_data": synthetic_data.to_dict(orient="records"),
            "quality_score": quality_report.get_score(),
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host = "localhost",port=8000)