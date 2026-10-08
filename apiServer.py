from fastapi import FastAPI
from pydantic import BaseModel
from mainTango import ETL_TANGO
from mainPICO import ETL_PICO
from mainOM import ETL_OM
from datetime import date
from generateOM_Transaction import generateOMDaily
from generatePAMF_Transaction import generateGLTransaction,generateFRONTTransaction
from reconciliation import main as reconcile_transaction
from mainAMS import ETL_AMS
from Check_transaction_before_reconciliation import check_unreconciled_transaction
from ETL import upload_reconciliation
app = FastAPI()
# ---------------------------
# Pydantic model
# ---------------------------

class DateRequest(BaseModel):
    requestDate: date  # expects YYYY-MM-DD

@app.post("/transformTangoTransaction")
def transformTangoTransaction(request: DateRequest):
    print('@app.post("/transformTangoTransaction")')
    d=request.requestDate
    try:
        result=ETL_TANGO(d)
        return result
    except Exception as e:
        print(e)
    


@app.post("/check_unreconciled_transaction")
def recheck_unreconciled_transaction(request: DateRequest):
    print('@app.post("/check_unreconciled_transaction")')
    d=request.requestDate
    try:
        result=check_unreconciled_transaction(d)
        return result
    
    except Exception as e:
        print(e)



@app.post("/transformPicoTransaction")
def transformPicoTransaction(request: DateRequest):
    print('@app.post("/transformPicoTransaction")')
    d=request.requestDate
    result=ETL_PICO(d)
    return result


@app.post("/transformOMTransaction")
def transformOMTransaction(request: DateRequest):
    print('@app.post("/transformOMTransaction")')
    d=request.requestDate
    result=ETL_OM(d)
    return result



@app.post("/transformAMS")
def transformAMS(request: DateRequest):
    print('@app.post("/transformAMS")')
    d=request.requestDate
    result=ETL_AMS(d)
    return result

@app.post("/generateOMMapping")
def generateOMMapping(request: DateRequest):
    d=request.requestDate
    result='result'
    result=generateOMDaily(d)
      
    return result


@app.post("/generateFrontTrx")
def generateFrontTrx(request: DateRequest):
    d=request.requestDate
    result='result'
    result=generateFRONTTransaction(d)

    return result

@app.post("/generateGLTrx")
def generateGLTrx(request: DateRequest):
    d=request.requestDate
    result='result'
    result=generateGLTransaction(d)

    return result


@app.post("/reconcile")
def reconcile(request: DateRequest):
    d=request.requestDate
    result='result'
    print('d')
    result=reconcile_transaction(d)

    return result
    
    
@app.post("/upload_reconciliation")
def ETL_reconciliation(request: DateRequest):
    d=request.requestDate
    result='result'
    result=upload_reconciliation(d)

    return result