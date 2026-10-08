# -*- coding: utf-8 -*-
"""
Reconciliation ETL for Ubuntu
"""

from sqlalchemy import create_engine, text
from datetime import datetime, date, timedelta
import pandas as pd
from urllib.parse import quote_plus

# ------------------------------
# 1️⃣ Database engine (Ubuntu-safe)
# ------------------------------
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.20.24.37;"
    "DATABASE=RECONCILIATION_DFS;"
    "UID=Minonja;"
    "PWD=Minonja;"
)
engine = create_engine("mssql+pyodbc:///?odbc_connect={}".format(quote_plus(conn_str)))

# ------------------------------
# 2️⃣ Helper functions
# ------------------------------
def update_process_status(id: int, new_status: str) -> int:
    update_query = """
    UPDATE [RECONCILIATION_DFS].[dbo].[reconciliation_reconciliationprocess]
    SET [status] = :new_status
    WHERE [id] = :id
    """
    with engine.begin() as conn:
        result = conn.execute(text(update_query), {"new_status": new_status, "id": id})
        return result.rowcount

def get_process_id(date_str: str) -> int:
    query = """
    SELECT id FROM [RECONCILIATION_DFS].[dbo].[reconciliation_reconciliationprocess]
    WHERE [date] = :date_val
    """
    df = pd.read_sql(text(query), engine, params={"date_val": date_str})
    return int(df['id'].iloc[0]) if not df.empty else None

from sqlalchemy import create_engine, text
import urllib

def generate_process(date_str: str) -> int:
    server   = '172.20.24.37'
    database = 'RECONCILIATION_DFS'
    username = 'Minonja'
    password = 'Minonja'

    params = urllib.parse.quote_plus(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    df_process = pd.DataFrame({
        'date':       [date_str],
        'status':     ['processing'],
        'created_at': [datetime.now()],
        'user_id':    [1],
        'is_cloture':    [0]
    })

    # ✅ Use engine.begin() to get a connection that auto-commits
    with engine.begin() as conn:
        df_process.to_sql(
            name='reconciliation_reconciliationprocess',
            con=conn,        # ✅ pass connection, not engine
            if_exists='append',
            index=False
        )

    
    return get_process_id(date_str)

def delete_table_by_date(table_name: str, date_col: str, date_val: str) -> int:
    query = f"DELETE FROM [RECONCILIATION_DFS].[dbo].[{table_name}] WHERE {date_col} = :date_val"
    with engine.begin() as conn:
        result = conn.execute(text(query), {"date_val": date_val})
        return result.rowcount

# ------------------------------
# 3️⃣ ETL Transformations
# ------------------------------
def tranform_transaction_type(technical_account):
    mapping = {
        '324820660':'repayment',
        '324820662':'disbursement',
        '324820678':'wallet_to_bank',
        '324820679':'bank_to_wallet',
    }
    return mapping.get(technical_account, "unknown")

#fixe the logic of reconciliation process after
def ETL_OM(date_date,process_id):
    dt=date_date.strftime("%Y%m%d")

    date_str = date_date.strftime("%Y-%m-%d")


    filename_reconcile_om= f"./output/reconciliation/dailyTransaction-reconciliation-OM-{dt}.xlsx"

    columns_data_type={
        'N°':int, 
        'Date':object, 
        'Heure':object, 
        'OMTransactionID':str, 
        'Service':str,
        'Statut':str, 
        'technical_account':str, 
        'debit':object, 
        'credit':object, 
        'TransactionDatetime':'datetime64[ns]',
        'transaction_type':str, 
        'operationID':str, 
        }


    columns_rename_for_pipeline={
        'N°':'no', 
        'status': 'reconciliation_status',
        'TransactionDatetime':'TransactionDateTime'
        }


    columns_list_for_destination_table =[
        'no'
        ,'Date'
        ,'Heure'
        ,'OMTransactionID'
        ,'technical_account'
        ,'debit'
        ,'credit'
        ,'TransactionDateTime'
        ,'transaction_type'
        ,'operationID'
        ,'RequestId'
        ,'match_probability'
        ,'reconciliation_status'
        ,'ticket_reference'
        ,'rollback_reference'
        ,'ReconciliationProcess_id'
    ]


    df_om = pd.read_excel(filename_reconcile_om,dtype=columns_data_type)
    
    print(df_om.dtypes)
    print(df_om.columns)
    df_om = df_om.drop(columns=['Unnamed: 0'], errors='ignore')
    missing_cols = [
        #'RequestId',
        'ticket_reference',
        'rollback_reference',
        'ReconciliationProcess_id'
    ]

    for col in missing_cols:
        if col not in df_om.columns:
            df_om[col] = None
            
    df_om = df_om.rename(columns=columns_rename_for_pipeline)

    df_om=df_om[columns_list_for_destination_table]


    

    df_om['ReconciliationProcess_id']=process_id

    df_om['transaction_type'] = df_om.apply(
        lambda row:tranform_transaction_type(row['technical_account']),
        axis=1
    )

    df_om.to_sql(
        name='reconciliation_reconciliationom',  # table name
        con=engine,
        if_exists='append',  # 'replace' or 'append'
        index=False
    )

    
    ctx={
        "code": 200,
        "Status": "success",
        "message": "OM Reconciliation Transaction Loaded to sql server"
    }
    return ctx

def ETL_AMS(date_date,process_id):
    
    dt=date_date.strftime("%Y%m%d")
    
    date_str = date_date.strftime("%Y-%m-%d")
    
    filename_reconcile_ams= f"./output/reconciliation/dailyTransaction-reconciliation-AMS-{dt}.xlsx"
    
    
    
    columns_data_type={
        'StatusAMS':object, #[StatusAMS]
        'StatusOM':object,# [StatusOM]
        'Amount':object, # [Amount]
        'RequestId':str, # [RequestId]
        'alias':str,#
        'uid_credit':str, #
        'operationID':str, # [operationID]
        'transactionDatetime':'datetime64[ns]', #[transactionDatetime]
        'Type':object, #[transaction_type]
        'is_duplicate':int,#
        'time_diff_min':float, #
        'match_probability':float,# [match_probability]
        'status':str#[reconciliation_status]
        }
    
    
    df_ams=pd.read_excel(filename_reconcile_ams,dtype=columns_data_type)
    
    columns_rename_for_pipeline={
        'status': 'reconciliation_status',
        'Type':'transaction_type',
        }
    
    df_ams = df_ams.rename(columns=columns_rename_for_pipeline)
    
    missing_cols = [
         
         'ticket_reference',
         'rollback_reference',
         'ReconciliationProcess_id',
         'OMTransactionID'
     ]
    
    for col in missing_cols:
         if col not in df_ams.columns:
             df_ams[col] = None
             
    columns_list_for_destination_table =[
        'StatusAMS'
        ,'StatusOM'
        ,'transaction_type'
        ,'Amount'
        ,'RequestId'
        ,'operationID'
        ,'OMTransactionID' # does not exist 
        ,'transactionDatetime'
        ,'match_probability'
        ,'reconciliation_status'
        ,'ticket_reference'
        ,'rollback_reference'
        ,'ReconciliationProcess_id'
    ]

    

    df_ams['ReconciliationProcess_id']=process_id
    
    df_ams=df_ams[columns_list_for_destination_table]

    df_ams['transactionDatetime'] = df_ams['transactionDatetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_ams.to_sql(
            name='reconciliation_reconciliationams',  # table name
            con=engine,
            if_exists='append',  # 'replace' or 'append'
            index=False
        )
    ctx={
        "code": 200,
        "Status": "success",
        "message": "AMS Reconciliation Transaction Loaded to sql server"
    }
    return ctx
def upload_reconciliation(dt):
    date_str = dt.strftime("%Y-%m-%d")
    
    try:
        print('----------------------------------->1')
        delete_table_by_date("reconciliation_reconciliationams","convert(varchar,[transactionDatetime],23)",date_str)
        print('----------------------------------->2')
        delete_table_by_date("reconciliation_reconciliationom","[Date]",date_str)
        print('----------------------------------->3')
        delete_table_by_date("reconciliation_reconciliationprocess","[date]",date_str)
        print('----------------------------------->4')

        process_id = generate_process(date_str)
        print('----------------------------------->5')
        ETL_OM(dt, process_id)
        print('----------------------------------->6')
        ETL_AMS(dt, process_id)
        print('----------------------------------->7')
        update_process_status(process_id,'done')
        print('----------------------------------->8')
        print(f"{date_str} processed successfully.")
        ctx={
          "code": 200,
          "Status": "success",
          "message": "Reconiliation Transaction Loaded"
          }
        return ctx
    except Exception as e:
        print(f"Error processing {date_str}: {e}")
        ctx={
          "code": 400,
          "Status": "Failed",
          "message": f"Error processing {date_str}: {e}"
          }
        return ctx

    