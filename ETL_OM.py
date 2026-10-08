# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 14:57:06 2026

@author: m.razakasoa
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 11:00:25 2026

@author: m.razakasoa
"""
from sqlalchemy import create_engine,text

from datetime import datetime,date
import pandas as pd
engine = create_engine(
    "mssql+pyodbc://Minonja:Minonja@172.20.24.37/RECONCILIATION_DFS?driver=SQL+Server"
)

def update_process_status(id: int, new_status: str) -> int:
    """
    Update the 'status' column for a specific date in reconciliation_reconciliationprocess.

    Args:
        date_val (str): Date in 'YYYY-MM-DD' format.
        new_status (str): New status to set.

    Returns:
        int: Number of rows updated.
    """
    update_query = """
    UPDATE [RECONCILIATION_DFS].[dbo].[reconciliation_reconciliationprocess]
    SET [status] = :new_status
    WHERE [id] = :id
    """

    # Use engine.begin() for auto-commit
    with engine.begin() as conn:
        result = conn.execute(text(update_query), {"new_status": new_status, "id": id})
        return result.rowcount  # number of rows updated
    
def get_process_id(date_str: str) -> int:
    """
    Get the id from reconciliation_reconciliationprocess for a given date.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        
    Returns:
        int: ID of the reconciliation process.
             Returns None if no record is found.
    """
    query = f"""
    SELECT id
    FROM [RECONCILIATION_DFS].[dbo].[reconciliation_reconciliationprocess]
    WHERE [date] = '{date_str}'
    """
    
    # Read the query into a DataFrame
    df = pd.read_sql(query, engine)
    
    # Return the ID as int if found
    if not df.empty:
        return int(df['id'].iloc[0])
    else:
        return None
    
def delete_process_by_date(date_str: str) -> int:
    """
    Delete reconciliation process rows for a specific date.

    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.

    Returns:
        int: Number of rows deleted.
    """
    delete_query = """
    DELETE FROM [RECONCILIATION_DFS].[dbo].[reconciliation_reconciliationprocess]
    WHERE [date] = :date_val
    """

    # Use engine.begin() to auto-commit at the end
    with engine.begin() as conn:
        result = conn.execute(text(delete_query), {"date_val": date_str})
        return result.rowcount  # number of rows deleted
    
def delete_reconciliation_om_by_date(date_str: str) -> int:
    """
    Delete reconciliation process rows for a specific date.

    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.

    Returns:
        int: Number of rows deleted.
    """
    delete_query = """
    DELETE FROM [RECONCILIATION_DFS].[dbo].[reconciliation_reconciliationom]
    WHERE [Date] = :date_str
    """

    # Use engine.begin() to auto-commit at the end
    with engine.begin() as conn:
        result = conn.execute(text(delete_query), {"date_str": date_str})
        return result.rowcount  # number of rows deleted    

def tranform_transaction_type(technical_account):
    dic_technical_account={
        '324820660':'repayment',
        '324820662':'disbursement',
        '324820678':'wallet_to_bank',
        '324820679':'bank_to_wallet',
        
        }
    return dic_technical_account[technical_account]





def ETM_OM(date_date):
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
        'RequestId',
        'ticket_reference',
        'rollback_reference',
        'ReconciliationProcess_id'
    ]

    for col in missing_cols:
        if col not in df_om.columns:
            df_om[col] = None
            
    df_om = df_om.rename(columns=columns_rename_for_pipeline)

    df_om=df_om[columns_list_for_destination_table]


    delete_reconciliation_om_by_date(date_str)# delete reconciliation om data
    delete_process_by_date(date_str)# delete reonciliation process

    dic_process = {
        'date': [date_date],
        'status': ['processing'],
        'created_at': [datetime.now()],
        'user_id': [1]
    }

    df_process = pd.DataFrame(dic_process)

    df_process.to_sql(
        name='reconciliation_reconciliationprocess',  # table name
        con=engine,
        if_exists='append',  # 'replace' or 'append'
        index=False
    )

    process_id=get_process_id(date_str)
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

    update_process_status(process_id,'done')


