# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 09:35:36 2026

@author: m.razakasoa
"""


from sqlalchemy import create_engine,text
from datetime import datetime,timedelta
import pandas as pd
import pyodbc
from mail import send_reconciliation_report
def get_merchant_transaction(date):
    con = pyodbc.connect('DRIVER={driver};SERVER=172.20.24.37;DATABASE=CBS;UID=Minonja;PWD=Minonja'.format(driver='ODBC Driver 17 for SQL Server'))#ODBC Driver 17 for SQL Server
    
    sql_mc_al = """
    SELECT  mc.RequestID, mc.AmountCRY, al.RequestDateCreated as PostingDate, al.RequestId, 
    sr.Name as apiService
    FROM cbs.dbo.mcTransaction mc 
    JOIN bagsPAMF_CBS_MC.dbo.apiLog al ON al.apiLogId = mc.RequestID
    JOIN bagsPAMF_CBS_MC.dbo.apiService sr on sr.apiServiceId = al.apiServiceId  
    WHERE mc.Status = 3 AND mc.rMerchantID = 4 and al.apiServiceID in (700,701,203,302) AND mc.PostingDate= '{date}'
    """.format(date=date)
    df_mc_al = pd.read_sql(sql_mc_al, con)
    return df_mc_al
def get_reconciliation_transaction(date_from,date_to):
    con = pyodbc.connect('DRIVER={driver};SERVER=172.20.24.37;DATABASE=CBS;UID=Minonja;PWD=Minonja'.format(driver='ODBC Driver 17 for SQL Server'))#ODBC Driver 17 for SQL Server
    sql_rec = """
    SELECT 
        RequestId, 
        OmMongoId, 
        DATEADD(hour, 3, TransactionDate) AS TransactionDate_Adjusted
    FROM [bagsPAMF_CBS_INTG].[dbo].[AllReconciliatedItems]
    WHERE CAST(TransactionDate AS DATE) BETWEEN '{date_from}' AND '{date_to}'
    ORDER BY TransactionDate DESC;
    """.format(date_from=date_from,date_to=date_to)
    
    
    df_rec = pd.read_sql(sql_rec, con)
    return df_rec


def get_connection():
    return create_engine(
        "mssql+pyodbc://Minonja:Minonja@172.20.24.37/RECONCILIATION_DFS"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

def generate_process(len_df,date):
    engine = get_connection()
    if len_df>0:
        status='{} transactions have to be reconcile'.format(len_df)
    else:
        status ='all transactions are reconciled correctly'
    dic_process = {
        'number_of_unreconciled': [len_df],
        'status': status,
        'created_at': [datetime.now()],
        'date':[date],
        'user_id': [1]
    }

    df_process = pd.DataFrame(dic_process)

    df_process.to_sql(
        name='allReconciliatedItemsSTATUS',  # table name
        con=engine,
        if_exists='append',  # 'replace' or 'append'
        index=False
    )

    
    return None
def delete_process_by_date(date_str: str) -> int:
    engine = get_connection()
    delete_query = """
        DELETE FROM [RECONCILIATION_DFS].[dbo].[allReconciliatedItemsSTATUS]
        WHERE [date] = :date_val
        """

    # Use engine.begin() to auto-commit at the end
    with engine.begin() as conn:
        result = conn.execute(text(delete_query), {"date_val": date_str})
        return result.rowcount  # number of rows deleted
def delete_unreconciled_by_date(date_str: str) -> int:
    engine = get_connection()
    delete_query = """
        delete  FROM [RECONCILIATION_DFS].[dbo].[UnreconciledTransaction]   where convert(varchar,[PostingDate],23) = :date_val
        """

    # Use engine.begin() to auto-commit at the end
    with engine.begin() as conn:
        result = conn.execute(text(delete_query), {"date_val": date_str})
        return result.rowcount  # number of rows deleted

def UPLOADMISSING(DF):
    engine = get_connection()
    
    DF = DF.rename(columns={
          "RequestID": "apiLogID",
      })
    mapping = {
    'LOAN: Loan Repayment': 'repayment',
    'LOAN: Confirm Loan Disbursement': 'disbursement',
    'ACCOUNT: Account Deposit': 'wallet_to_bank',
    'ACCOUNT: Account Withdrawal': 'bank_to_wallet'
    }
    DF['transaction_type'] = DF['apiService'].map(mapping)
    DF['is_reconciled']= False
    DF.to_sql( 
        name='UnreconciledTransaction',  # table name
        con=engine,
        if_exists='append',  # 'replace' or 'append'
        index=False
    )   
     
def check_unreconciled_transaction(reconciliation_date):
    
    date_from = reconciliation_date + timedelta(days=-1)
    date_to = reconciliation_date + timedelta(days=1)
    
    date_from=date_from.strftime("%Y-%m-%d")
    reconciliation_date=reconciliation_date.strftime("%Y-%m-%d")
    date_to=date_to.strftime("%Y-%m-%d")
    print('*'*100)
    print('reconciliation_date:', reconciliation_date)
    
    df_mc_al=get_merchant_transaction(reconciliation_date)
    df_rec = get_reconciliation_transaction(date_from,date_to)
    # Left merge to find records missing in rec
    df = df_mc_al.merge(df_rec, left_on='RequestId', right_on='RequestId', how='left')
    missing = df[df['OmMongoId'].isna()]
    delete_process_by_date(reconciliation_date)
    delete_unreconciled_by_date(reconciliation_date)
    
    if len(missing)>0:
        generate_process(len(missing),reconciliation_date)
        send_reconciliation_report(reconciliation_date,success=False,df_errors=missing)
        UPLOADMISSING(missing)
        print('inserted...')
        
    else:
        send_reconciliation_report(reconciliation_date,success=True,df_errors=None)
        generate_process(len(missing),reconciliation_date)
        print('inserted...')
    print('*'*100)
    ctx={
        "code": 200,
        "Status": "success",
        "message": "Reconciliation Checked"
    }
    return ctx
    
     
if __name__ == "__main__":
    d=-2
    

