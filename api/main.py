import json
import sys
import os
import pandas as pd
import numpy as np
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

# Add the directory containing the 'api' module to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (DropDuplicatesResponse, DropExportDuplicatesInput, 
                        DropExportDuplicatesResponse, ErrorHandlingInput, 
                        PreliminaryTestResponse, UniqueIDResponse, 
                        UniqueIDCheckInput, UniqueIDCheckResponse, 
                        DuplicateAnalysisResponse, L1SampleSizeInput, 
                        L2SampleSizeInput, ThirdPartySamplingInput)
from api.utils import (analyze_frequency_table, analyze_indicator_fill_rate, 
                       analyze_missing_entries, analyze_zero_entries, 
                       dropFullDuplicates, error_handling, findUniqueIDs, 
                       uniqueIDcheck, dropExportDuplicates, percentDuplicated, 
                       run_preliminary_tests, l1_sample_size_calculator, 
                       l2_sample_size_calculator, third_party_sampling_strategy)
from api.database import get_db, UploadedFile
from api.database import engine, Base


app = FastAPI()

# Global variable to store the last processed data
last_processed_data = {
    'unique_rows': None,
    'duplicate_rows': None
}

# Global variable to store the last deduplicated data
last_deduplicated_data = None

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if a file with the same name already exists
    existing_file = db.query(UploadedFile).filter(UploadedFile.filename == file.filename).first()
    
    if existing_file:
        return JSONResponse(
            status_code=409,  # Conflict
            content={"message": f"A file with the name '{file.filename}' already exists.", "id": existing_file.id}
        )

    # Proceed with saving the file if it doesn't exist
    contents = await file.read()
    db_file = UploadedFile(filename=file.filename, content=contents)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {"message": "File uploaded successfully", "id": db_file.id}


@app.get("/list_files")
async def list_files(db: Session = Depends(get_db)):
    files = db.query(UploadedFile.id, UploadedFile.filename).all()
    return [{"id": file.id, "filename": file.filename} for file in files]

@app.get("/get_file/{file_id}")
async def get_file(file_id: int, db: Session = Depends(get_db)):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file content and filename as JSON
    return {
        "filename": file.filename,
        "content": file.content.decode('latin1')  # Decode binary content for JSON compatibility
    }

@app.post("/preliminary_tests", response_model=PreliminaryTestResponse)
async def preliminary_tests(file: UploadFile = File(None), file_id: int = None, db: Session = Depends(get_db)):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")
        
        df = pd.read_csv(io.BytesIO(contents))
        result = run_preliminary_tests(df)
        return PreliminaryTestResponse(**result)
    except Exception as e:
        print(f"Error in preliminary_tests: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/find_unique_ids", response_model=List[UniqueIDResponse])
async def find_unique_ids(file: UploadFile = File(None), file_id: int = None, db: Session = Depends(get_db)):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents))
        result = findUniqueIDs(df.to_dict('records'))
        return [UniqueIDResponse(UniqueID=item['UniqueID'], Numeric_DataTypes=item['Numeric_DataTypes']) for item in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/unique_id_check", response_model=UniqueIDCheckResponse)
async def unique_id_check(input_data: UniqueIDCheckInput):
    try:
        df = pd.DataFrame(input_data.data)
        result = uniqueIDcheck(df.to_dict('records'), input_data.columns)
        return UniqueIDCheckResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/drop_export_duplicates", response_model=DropExportDuplicatesResponse)
async def drop_export_duplicates(
    file: UploadFile = File(None),
    file_id: int = None,
    input_data: str = Form(...),
    db: Session = Depends(get_db)
):
    global last_processed_data
    try:
        input_params = json.loads(input_data)
        input_model = DropExportDuplicatesInput(**input_params)
        
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents), keep_default_na=False, na_values=[''])
        
        unique_rows, duplicate_rows = dropExportDuplicates(
            df,
            input_model.uidCol,
            input_model.keptRow,
            input_model.export,
            input_model.chunksize
        )
        
        unique_count = len(unique_rows)
        duplicate_count = len(duplicate_rows) if duplicate_rows is not None else 0
        total_count = unique_count + duplicate_count
        percent_duplicates = (duplicate_count / total_count) * 100 if total_count > 0 else 0

        # Store the processed data
        last_processed_data['unique_rows'] = pd.DataFrame(unique_rows)
        last_processed_data['duplicate_rows'] = pd.DataFrame(duplicate_rows) if duplicate_rows is not None else None
        
        return DropExportDuplicatesResponse(
            unique_count=unique_count,
            duplicate_count=duplicate_count,
            percent_duplicates=percent_duplicates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_processed_data")
async def get_processed_data(data_type: str = Query(...), filename: str = Query(...)):
    global last_processed_data
    if data_type not in ['unique', 'duplicate']:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    data = last_processed_data['unique_rows'] if data_type == 'unique' else last_processed_data['duplicate_rows']
    
    if data is not None:
        csv_data = data.to_csv(index=False)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=404, detail=f"No {data_type} data available")

@app.get("/get_dataframe")
async def get_dataframe(data_type: str = Query(...)):
    global last_processed_data
    if data_type not in ['unique', 'duplicate']:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    data = last_processed_data['unique_rows'] if data_type == 'unique' else last_processed_data['duplicate_rows']
    
    if data is not None:
        return data.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict(orient='records')
    else:
        raise HTTPException(status_code=404, detail=f"No {data_type} data available")
    
@app.post("/duplicate_analysis", response_model=DuplicateAnalysisResponse)
async def duplicate_analysis(file: UploadFile = File(None), file_id: int = None, db: Session = Depends(get_db)):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents))
        num_duplicates, percent_duplicates = percentDuplicated(df)
        return DuplicateAnalysisResponse(num_duplicates=num_duplicates, percent_duplicates=percent_duplicates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove_duplicates", response_model=DropDuplicatesResponse)
async def remove_duplicates(
    file: UploadFile = File(None),
    file_id: int = None,
    remove_option: str = Form(...),
    db: Session = Depends(get_db)
):
    global last_deduplicated_data
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents))
        original_count = len(df)
        
        if remove_option == "Keep first occurrence":
            deduped_data = dropFullDuplicates(df.to_dict('records'), keep="first")
        elif remove_option == "Drop all occurrences":
            deduped_data = dropFullDuplicates(df.to_dict('records'), keep=False)
        else:
            raise HTTPException(status_code=400, detail="Invalid remove option")

        deduplicated_count = len(deduped_data)
        dropped_count = original_count - deduplicated_count

        # Store the deduplicated data for later retrieval
        last_deduplicated_data = deduped_data

        return DropDuplicatesResponse(
            original_count=original_count,
            deduplicated_count=deduplicated_count,
            dropped_count=dropped_count
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_deduplicated_data")
async def get_deduplicated_data(filename: str = Query("deduplicated_data.csv")):
    global last_deduplicated_data
    if last_deduplicated_data is not None:
        df = pd.DataFrame(last_deduplicated_data)
        csv_data = df.to_csv(index=False)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=404, detail="No deduplicated data available")
    
@app.post("/missing_entries")
async def missing_entries(
    file: UploadFile = File(None),
    file_id: int = None,
    input_data: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents), index_col=False)

        # Parse the input data
        input_data = json.loads(input_data)
        column_to_analyze = input_data["column_to_analyze"]
        group_by = input_data.get("group_by")
        filter_by = input_data.get("filter_by")

        # Validate input
        if column_to_analyze not in df.columns:
            raise ValueError(f"Column '{column_to_analyze}' not found in the dataset")
        
        if group_by and group_by not in df.columns:
            raise ValueError(f"Group by column '{group_by}' not found in the dataset")
        
        if filter_by:
            for col, value in filter_by.items():
                if col not in df.columns:
                    raise ValueError(f"Filter column '{col}' not found in the dataset")
                if df[df[col] == value].empty:
                    raise ValueError(f"No data found for filter: {col} = {value}")

        # Perform the analysis
        result = analyze_missing_entries(
            df, 
            column_to_analyze, 
            group_by, 
            filter_by
        )

        # Convert numpy types to Python native types for JSON serialization
        if isinstance(result['analysis'], dict):
            result['analysis'] = {
                k: (int(v[0]), float(v[1]) if not np.isnan(v[1]) and not np.isinf(v[1]) else None) 
                for k, v in result['analysis'].items()
            }
        else:
            result['analysis'] = (
                int(result['analysis'][0]), 
                float(result['analysis'][1]) if not np.isnan(result['analysis'][1]) and not np.isinf(result['analysis'][1]) else None
            )

        # Include rows with missing entries
        missing_rows = df[df[column_to_analyze].isna()]
        missing_rows_table = missing_rows.reset_index().to_dict(orient='records')
        
        # Convert any non-serializable values to None
        for row in missing_rows_table:
            for key, value in row.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    row[key] = None
                elif pd.isna(value):
                    row[key] = None

        result["missing_entries_table"] = missing_rows_table

        return JSONResponse(content=result)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@app.post("/zero_entries")
async def zero_entries(
    file: UploadFile = File(None),
    file_id: int = None,
    input_data: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        # Load the CSV file into a DataFrame
        df = pd.read_csv(io.BytesIO(contents))

        # Clean and normalize column names
        df.columns = df.columns.str.strip().str.lower()  # Strips whitespace and converts to lowercase
        print(f"Column names: {df.columns.tolist()}")  # Print out the column names for debugging

        # Parse the input data
        input_data = json.loads(input_data)
        column_to_analyze = input_data["column_to_analyze"].strip().lower()  # Normalize user input as well
        group_by = input_data.get("group_by")
        filter_by = input_data.get("filter_by")

        # Validate input
        if column_to_analyze not in df.columns:
            raise ValueError(f"Column '{column_to_analyze}' not found in the dataset: {df.columns.tolist()}")

        if group_by and group_by not in df.columns:
            raise ValueError(f"Group by column '{group_by}' not found in the dataset")

        if filter_by:
            for col in filter_by.keys():
                if col not in df.columns:
                    raise ValueError(f"Filter column '{col}' not found in the dataset")

        # Perform the analysis
        result = analyze_zero_entries(
            df, 
            column_to_analyze, 
            group_by, 
            filter_by
        )

        # Convert numpy types to Python native types for JSON serialization
        if isinstance(result['analysis'], dict):
            result['analysis'] = {k: (int(v[0]), float(v[1])) for k, v in result['analysis'].items()}
        else:
            result['analysis'] = (int(result['analysis'][0]), float(result['analysis'][1]))

        # Convert any non-serializable values to None in zero_entries_table
        for row in result["zero_entries_table"]:
            for key, value in row.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    row[key] = None
                elif pd.isna(value):
                    row[key] = None

        return JSONResponse(content=result)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/indicator_fill_rate")
async def indicator_fill_rate(
    file: UploadFile = File(None),
    file_id: int = None,
    input_data: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents))

        # Parse the input data
        input_data = json.loads(input_data)
        column_to_analyze = input_data["column_to_analyze"]
        group_by = input_data.get("group_by")
        filter_by = input_data.get("filter_by")
        invalid_condition = input_data.get("invalid_condition")
        include_zero_as_separate_category = input_data.get("include_zero_as_separate_category", True)

        # Validate input
        if column_to_analyze not in df.columns:
            raise ValueError(f"Column '{column_to_analyze}' not found in the dataset")
        
        if group_by and group_by not in df.columns:
            raise ValueError(f"Group by column '{group_by}' not found in the dataset")
        
        if filter_by:
            for col in filter_by.keys():
                if col not in df.columns:
                    raise ValueError(f"Filter column '{col}' not found in the dataset")

        # Perform the analysis
        result = analyze_indicator_fill_rate(
            df, 
            column_to_analyze, 
            group_by, 
            filter_by,
            invalid_condition,
            include_zero_as_separate_category
        )

        # Convert DataFrame to dict for JSON serialization
        if isinstance(result['analysis'], dict):
            result['analysis'] = {k: v.to_dict() for k, v in result['analysis'].items()}
        elif isinstance(result['analysis'], pd.DataFrame):
            if include_zero_as_separate_category:
                result['analysis'] = result['analysis'].to_dict()
            else:
                result['analysis'] = result['analysis'][result['analysis']['Category'] != 'Zero'].to_dict()
        else:
            # If it's neither a dict nor a DataFrame, convert to a serializable format
            result['analysis'] = json.loads(json.dumps(result['analysis'], default=str))

        # Convert any non-serializable values to None in detailed_data
        def clean_data(data):
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            elif isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
                return None
            elif pd.isna(data):
                return None
            else:
                return data

        result['detailed_data'] = clean_data(result['detailed_data'])

        return JSONResponse(content=result)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/frequency_table")
async def frequency_table(
    file: UploadFile = File(None),
    file_id: int = None,
    input_data: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if file:
            contents = await file.read()
        elif file_id:
            stored_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if not stored_file:
                raise HTTPException(status_code=404, detail="File not found")
            contents = stored_file.content
        else:
            raise HTTPException(status_code=400, detail="Either file or file_id must be provided")

        df = pd.read_csv(io.BytesIO(contents))

        # Parse the input data
        input_data = json.loads(input_data)
        column_to_analyze = input_data["column_to_analyze"]
        top_n = input_data.get("top_n", 5)
        group_by = input_data.get("group_by")
        filter_by = input_data.get("filter_by")

        # Validate input
        if column_to_analyze not in df.columns:
            raise ValueError(f"Column '{column_to_analyze}' not found in the dataset")
        
        if group_by and group_by not in df.columns:
            raise ValueError(f"Group by column '{group_by}' not found in the dataset")
        
        if filter_by:
            for col in filter_by.keys():
                if col not in df.columns:
                    raise ValueError(f"Filter column '{col}' not found in the dataset")

        # Perform the analysis
        result = analyze_frequency_table(
            df, 
            column_to_analyze, 
            top_n,
            group_by, 
            filter_by
        )

        # Convert DataFrame to dict for JSON serialization
        if isinstance(result['analysis'], dict):
            result['analysis'] = {k: (v[0].to_dict(orient='records'), v[1].to_dict(orient='records')) for k, v in result['analysis'].items()}
        else:
            result['analysis'] = (result['analysis'][0].to_dict(orient='records'), result['analysis'][1].to_dict(orient='records'))

        return JSONResponse(content=result)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/error-handling")
async def check_errors(input_data: ErrorHandlingInput):
    error_status, error_message = error_handling(input_data.params)
    return {"status": error_status, "message": error_message}    

@app.post("/l1-sample-size")
async def calculate_l1_sample_size(input_data: L1SampleSizeInput):
    result = l1_sample_size_calculator(input_data.dict())
    if result['status'] == 0:
        raise HTTPException(status_code=400, detail=result['message'])
    return result

@app.post("/l2-sample-size")
async def calculate_l2_sample_size(input_data: L2SampleSizeInput):
    result = l2_sample_size_calculator(input_data.dict())
    if result['status'] == 0:
        raise HTTPException(status_code=400, detail=result['message'])
    return result

@app.post("/third-party-sampling")
async def predict_third_party_sampling(input_data: ThirdPartySamplingInput):
    result = third_party_sampling_strategy(input_data.dict())
    if result['status'] == 0:
        raise HTTPException(status_code=400, detail=result['message'])
    return result