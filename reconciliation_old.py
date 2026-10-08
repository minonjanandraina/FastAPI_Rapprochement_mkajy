# -*- coding: utf-8 -*-
"""
Created on Tue Jan 20 09:32:53 2026

@author: m.razakasoa
"""
from urllib.parse import quote_plus
import pandas as pd

import numpy as np
from pathlib import Path
# 2️⃣ Define a function to get the tuple or keep original
def get_updated_row(row):
    if row['RequestId'] in request_map:
        vals = request_map[row['RequestId']]
        return pd.Series([vals['mcTransactionID'], vals['rAutoTransactionID'], vals['transactionAmount']])
    else:
        return pd.Series([row['mcTransactionID'], row['rAutoTransactionID'], row['transactionAmount']])
    
def get_updated_row_forFront(row):
    if row['RequestId'] in request_mapforFront:
        vals = request_mapforFront[row['RequestId']]
        return pd.Series([vals['technical_account'],vals['OMTransactionID'],vals['debit'], vals['credit'], vals['CheckAmount']])
    else:
        return pd.Series([row['technical_account'],row['OMTransactionID'],row['debit'], row['credit'], row['CheckAmount']])
    
def reconciliationStatus(refTransaction, AmountA, AmountB):
    if pd.isna(refTransaction):
        return 'Orphan'
    elif AmountA - AmountB > 0:
        return 'Error Amount'
    else:
        return 'Normale'


def get_and_upload_data(d):
    
    filename_csv_om =  f"./output/OM/dailyOMTransaction-mkajy-{d:%Y-%m-%d}.csv"
    
    filename_csv_front =  f"./output/FRONT/dailyFRONTTransaction-mkajy-{d:%Y-%m-%d}.csv"
    col_om = ['Date', 'Heure', 'OMTransactionID', 'Service', 'Statut',
           'technical_account', 'debit', 'credit', 'TransactionDatetime',
           'transaction_type', 'operationID', 'RequestId']

    
    col_front=[ 'RequestId', 'rAutoTransactionID', 'documentID',
           'transactionAmount', 'RequestDateCreated', 'rTransactionTypeID',
           'mcTransactionID', 'apiLogId']
    
    
    df_OM = pd.read_csv(filename_csv_om)
    
    df_FRONT = pd.read_csv(filename_csv_front)
    print(df_OM.columns)
    df_OM=df_OM[col_om]
    
    df_FRONT=df_FRONT[col_front]
    
    
    # ---- FIX DATE COLUMN (OM) ----
    df_OM["Date"] = (
        df_OM["Date"]
        .astype(str)
        .str.strip()
    )
    
    df_OM["Date"] = pd.to_datetime(
        df_OM["Date"],
        format="%d/%m/%Y",
        errors="coerce"
    )
    
    df_OM["Date"] = df_OM["Date"].dt.date
    
    df_OM = df_OM.rename(columns={
        'Statut': 'Status',
    })
    
    '''
    df_OM.to_sql("trx_transaction_OM",engine,if_exists="append",index=False,method="multi",chunksize=500)
    
    df_GL.to_sql("trx_transaction_GL",engine,if_exists="append",index=False,method="multi",chunksize=500)
    
    df_FRONT.to_sql("trx_transaction_front",engine,if_exists="append",index=False,method="multi",chunksize=500)
    '''
    return (df_OM,df_FRONT)

def reconcile_day(d):
    """
    *******What this function do? *******
    this function is used to do the reconciliation process between OM and FRONT transactions,
    it will take the date as input and return the reconciliation result for that date, we can also save 
    the reconciliation result in a csv file for further analysis and to aliment the database with a separate JOB 
    for the reconciliation process, in fact, we can create a table in the database to store the reconciliation
    result and then we can use this table to do some analysis and to create some dashboards and to manage failed transactions.
    
    """
    
    # Step 1: Get the data from the csv files and upload it to the database but we commented the upload part for now,
    # we will do it in a separate JOB for the reconciliation process, 
    # in fact, we can create a table in the database to store the reconciliation result and then we can use 
    # this table to do some analysis and to create some dashboards and to manage failed transactions.
    df_OM, df_FRONT = get_and_upload_data(d)

    
    # step 2: do the reconciliation process, 
    # in fact, we have to compare the transactions from OM and FRONT and check if they are consistent or not, 
    # for that we will use the RequestId as a key to compare the transactions, 
    # if the RequestId is not present in one of the two tables, 
    # we will consider it as an orphan transaction, 
    # if the RequestId is present in both tables but the amount is different, 
    # we will consider it as an error amount transaction, otherwise, we will consider it as a normal transaction.
    
    #join the two tables on RequestId to have all the transactions in one table and then we will do the reconciliation process,
    df_OM_FRONT_left_om = pd.merge(df_OM, df_FRONT, how='left', on='RequestId')
    df_OM_FRONT_left_front = pd.merge(df_FRONT, df_OM, how='left', on='RequestId')

    #formqte the transactions tables for OM and FRONT with the necessary columns for the reconciliation process,
    col_om_trx = [
        'Date', 'Heure', 'OMTransactionID', 'Service', 'Status',
        'technical_account', 'debit', 'credit', 'TransactionDatetime',
        'transaction_type', 'operationID', 'RequestId', 'mcTransactionID',
        'rAutoTransactionID', 'transactionAmount'
    ]
    col_front_trx = [
        'RequestId', 'rAutoTransactionID', 'documentID', 'transactionAmount',
        'RequestDateCreated', 'rTransactionTypeID', 'mcTransactionID',
        'apiLogId', 'technical_account', 'OMTransactionID', 'debit', 'credit'
    ]

    df_transaction_om = df_OM_FRONT_left_om[col_om_trx].copy()
    df_transaction_front = df_OM_FRONT_left_front[col_front_trx].copy()
    
    
    #process amount check and reconciliation status, 
    # in fact, we will create a new column called 'CheckAmount' 
    # which is the sum of debit and credit columns, 
    # then we will create another column called 'reconciliation_status' which will have the value 'Orphane' if the RequestId is not present in the other table, 
    # 'Error Amount' if the CheckAmount is different from the transactionAmount and 'Normale' if the CheckAmount is equal to the transactionAmount.
    df_transaction_front['CheckAmount'] = df_transaction_front['debit'] + df_transaction_front['credit']
    df_transaction_front['reconciliation_status'] = np.where(
        df_transaction_front['OMTransactionID'].isna(),
        'Orphan',
        np.where(
            df_transaction_front['CheckAmount'] != df_transaction_front['transactionAmount'],
            'Error Amount',
            'Normale'
        )
    )

    df_transaction_om['CheckAmount'] = df_transaction_om['debit'] + df_transaction_om['credit']
    df_transaction_om['reconciliation_status'] = np.where(
        df_transaction_om['mcTransactionID'].isna(),
        'Orphan',
        np.where(
            df_transaction_om['CheckAmount'] != df_transaction_om['transactionAmount'],
            'Error Amount',
            'Normale'
        )
    )

    df_transaction_om['RequestId'] = df_transaction_om['RequestId'].astype(str)
    df_transaction_front['RequestId'] = df_transaction_front['RequestId'].astype(str)

    #Now we have orphane transactions in both tables, 
    # in fact, we have to check if the orphane transactions in one table are present in the other table but with a different transaction type, 
    # for that we will create a new status called 'different Transaction Type' and we will update the reconciliation_status 
    # column with this status if the RequestId is present in the other table but with a different transaction type, for that we will use the 
    # list of orphane transactions from both tables and we will check if they are present in the other table or not, if they are present in the other 
    # table we will update the reconciliation_status column with the new status 'different Transaction Type'.
    list_om_orphane = df_transaction_om[df_transaction_om['reconciliation_status'] == 'Orphan']['RequestId'].tolist()
    list_front_orphane = df_transaction_front[df_transaction_front['reconciliation_status'] == 'Orphan']['RequestId'].tolist()

    df_transaction_om.loc[
        df_transaction_om['RequestId'].isin(list_front_orphane),
        'reconciliation_status'
    ] = 'different Transaction Type'

    df_transaction_front.loc[
        df_transaction_front['RequestId'].isin(list_om_orphane),
        'reconciliation_status'
    ] = 'different Transaction Type'

    global request_map
    df_map = df_transaction_front[df_transaction_front['reconciliation_status'] == 'different Transaction Type']
    request_map = df_map.set_index('RequestId')[['mcTransactionID', 'rAutoTransactionID', 'transactionAmount']].to_dict('index')
    df_transaction_om[['mcTransactionID', 'rAutoTransactionID', 'transactionAmount']] = df_transaction_om.apply(get_updated_row, axis=1)

    global request_mapforFront
    df_map_forFront = df_transaction_om[df_transaction_om['reconciliation_status'] == 'different Transaction Type']
    request_mapforFront = df_map_forFront.set_index('RequestId')[['technical_account', 'OMTransactionID', 'debit', 'credit', 'CheckAmount']].to_dict('index')
    df_transaction_front[['technical_account', 'OMTransactionID', 'debit', 'credit', 'CheckAmount']] = df_transaction_front.apply(get_updated_row_forFront, axis=1)

    #generate file for the reconciliation result, 
    # we will save the reconciliation result in a csv file 
    # for further analysis and to aliment the database with a separate 
    # JOB for the reconciliation process, in fact, 
    # we can create a table in the database to store the reconciliation result and then we can
    # use this table to do some analysis and to create some dashboards and to manage failed transactions.
    output_dir = Path("./output/reconciliation")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_om = output_dir / f"reconciliation_om-mkajy-{d:%Y-%m-%d}.csv"
    output_file_front = output_dir / f"reconciliation_front-mkajy-{d:%Y-%m-%d}.csv"

    df_transaction_om.to_csv(output_file_om, index=False)
    df_transaction_front.to_csv(output_file_front, index=False)
    # for more convenience we write the 2 dataframe in one excel file with 2 sheets one for OM and the other for FRONT
    output_file_excel = output_dir / f"reconciliation_result-mkajy-{d:%Y-%m-%d}.xlsx"
    with pd.ExcelWriter(output_file_excel) as writer:
        df_transaction_om.to_excel(writer, sheet_name='OM', index=False)
        df_transaction_front.to_excel(writer, sheet_name='FRONT', index=False)

    result = {
        "date": f"{d:%Y-%m-%d}",
        "total_transactions_OM": int(len(df_transaction_om)),
        "total_transactions_FRONT": int(len(df_transaction_front)),
        "orphane_transactions_OM": int((df_transaction_om['reconciliation_status'] == 'Orphan').sum()),
        "orphane_transactions_FRONT": int((df_transaction_front['reconciliation_status'] == 'Orphan').sum()),
        "error_amount_transactions_OM": int((df_transaction_om['reconciliation_status'] == 'Error Amount').sum()),
        "error_amount_transactions_FRONT": int((df_transaction_front['reconciliation_status'] == 'Error Amount').sum()),
        "normal_transactions_OM": int((df_transaction_om['reconciliation_status'] == 'Normale').sum()),
        "normal_transactions_FRONT": int((df_transaction_front['reconciliation_status'] == 'Normale').sum())
    }

    return result



"""
##Starting from here we have to do the reconciliation process, in fact, we have to compare the transactions from OM and FRONT and check if they are consistent or not, for that we will use the RequestId as a key to compare the transactions, if the RequestId is not present in one of the two tables, we will consider it as an orphan transaction, if the RequestId is present in both tables but the amount is different, we will consider it as an error amount transaction, otherwise, we will consider it as a normal transaction.
# need to convert the following to function and put it in apiServer.py and call it in the main function, the function will take the date as input and return the reconciliation result for that date, we can also save the reconciliation result in a csv file for further analysis.
#input : date
#
#ouput : json with the following structure:
'''{
    "date": "2026-01-01",
    "total_transactions_OM": 100,
    "total_transactions_FRONT": 100,
    "orphane_transactions_OM": 10,
    "orphane_transactions_FRONT": 10,
    "error_amount_transactions_OM": 5,
    "error_amount_transactions_FRONT": 5,
    "normal_transactions_OM": 85,
    "normal_transactions_FRONT": 85
} + file in output/reconciliation/reconciliation_result-mkajy-2026-01-01.csv
'''
# bornes
start = date(2026, 1, 1)
end = date(2026, 2,5)

# création de la liste
list_date = [start + timedelta(days=i) for i in range((end - start).days + 1)]

df_transaction_om_full =pd.DataFrame()
df_transaction_front_full =pd.DataFrame()
df_OM_full=pd.DataFrame()
df_FRONT_full=pd.DataFrame()
for dt in list_date:
    print('*-'*30)
    print(dt)
    
    
    filename_csv_orph_OM_FRONT =  f"./output/ORPH/orph_OM_FRONT-mkajy-{dt:%Y-%m-%d}.xlsx"
    filename_csv_orph_FRONT_OM =  f"./output/ORPH/orph_FRONT_OM-mkajy-{dt:%Y-%m-%d}.xlsx"
    df_OM,df_FRONT= get_and_upload_data(dt)
    df_OM_full = pd.concat([df_OM_full,df_OM],ignore_index=True)
    df_FRONT_full = pd.concat([df_FRONT_full,df_FRONT],ignore_index=True)

        
    df_OM_FRONT_left_om = pd.merge(df_OM, df_FRONT,how='left',on='RequestId')
    df_OM_FRONT_left_front = pd.merge(df_FRONT,df_OM,how='left',on='RequestId')
    
    

    
    print('*-'*30)


    col_om_trx=['Date', 'Heure', 'OMTransactionID', 'Service', 'Status',
        'technical_account', 'debit', 'credit', 'TransactionDatetime',
        'transaction_type', 'operationID', 'RequestId','mcTransactionID','rAutoTransactionID','transactionAmount']
    
    col_front_trx=['RequestId', 'rAutoTransactionID', 'documentID', 'transactionAmount',
        'RequestDateCreated', 'rTransactionTypeID', 'mcTransactionID',
        'apiLogId','technical_account','OMTransactionID','debit', 'credit']
    
    df_transaction_om = df_OM_FRONT_left_om[col_om_trx]
    
    df_transaction_front = df_OM_FRONT_left_front[col_front_trx]
    
    df_transaction_om_full=pd.concat([df_transaction_om_full,df_transaction_om],ignore_index=True)
    df_transaction_front_full= pd.concat([df_transaction_front_full,df_transaction_front],ignore_index=True)
    


#process

df_transaction_front_full['CheckAmount']=df_transaction_front_full['debit']+df_transaction_om_full['credit']
df_transaction_front_full['reconciliation_status'] = np.where(
    df_transaction_front_full['OMTransactionID'].isna(),
    'Orphane',
    np.where(
        df_transaction_front_full['CheckAmount'] != df_transaction_front_full['transactionAmount'],
        'Error Amount',
        'Normale'
    )
)


df_transaction_om_full['CheckAmount']=df_transaction_om_full['debit']+df_transaction_om_full['credit']
df_transaction_om_full['reconciliation_status'] = np.where(
    df_transaction_om_full['mcTransactionID'].isna(),
    'Orphane',
    np.where(
        df_transaction_om_full['CheckAmount'] != df_transaction_om_full['transactionAmount'],
        'Error Amount',
        'Normale'
    )
)



print('Extraction ----'*10)

df_transaction_om_full['RequestId'] = df_transaction_om_full['RequestId'].astype(str)
df_transaction_front_full['RequestId'] = df_transaction_front_full['RequestId'].astype(str)

# des fois les transactions de remboursement sont converties en transaction de dépôt, en effet, il faut rajouter un autre status 'different Transaction Type

list_om_orphane =df_transaction_om_full[df_transaction_om_full['reconciliation_status']=='Orphane']['RequestId'].tolist()
list_front_orphane =df_transaction_front_full[df_transaction_front_full['reconciliation_status']=='Orphane']['RequestId'].tolist()

# Update the 'reconciliation_status' column
df_transaction_om_full.loc[
                        df_transaction_om_full['RequestId'].isin(list_front_orphane),
                        'reconciliation_status'
] = 'different Transaction Type'  # or whatever value you want
                    

# Update the 'reconciliation_status' column
df_transaction_front_full.loc[
                        df_transaction_front_full['RequestId'].isin(list_om_orphane),
                        'reconciliation_status'
] = 'different Transaction Type'  # or whatever value you want
                    

df_map = df_transaction_front_full[df_transaction_front_full['reconciliation_status']=='different Transaction Type']
request_map = df_map.set_index('RequestId')[['mcTransactionID', 'rAutoTransactionID', 'transactionAmount']].to_dict('index')
df_transaction_om_full[['mcTransactionID', 'rAutoTransactionID', 'transactionAmount']] = df_transaction_om_full.apply(get_updated_row, axis=1)



df_map_forFront = df_transaction_om_full[df_transaction_om_full['reconciliation_status']=='different Transaction Type']
request_mapforFront = df_map_forFront.set_index('RequestId')[['technical_account','OMTransactionID','debit', 'credit', 'CheckAmount']].to_dict('index')
df_transaction_front_full[['technical_account','OMTransactionID','debit', 'credit', 'CheckAmount']] = df_transaction_front_full.apply(get_updated_row_forFront, axis=1)


"""