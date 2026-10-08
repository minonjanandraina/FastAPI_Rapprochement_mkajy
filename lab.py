# -*- coding: utf-8 -*-
"""
Created on Tue Feb  3 10:52:09 2026

@author: m.razakasoa
"""

import calendar
import pandas as pd
from datetime import date, datetime, timedelta
from exceptions import  dataCleanningError
from util import getMappingAMS, getMatched,checkMappedData

def safe_read_csv(path: str, sep=","):
    """Read CSV safely and return None if not found."""
    try:
        print("Reading:", path)
        return pd.read_csv(path, sep=sep)
    except Exception:
        return None





d=date(2026,1,2)

filename = f"./staggingArea/OM/DailyOMTransaction-mkajy-{d:%Y%m%d}.csv"
print(filename)
df_om = pd.read_csv(filename)
print(filename, "len current", len(df_om))
filename =  f"./staggingArea/PAMF/dailyPAMFTransaction-mkajy-{d:%Y-%m-%d}.csv"
print(filename)
df_ams = pd.read_csv(filename,sep=',')
    


df_om["nb_digits"] = df_om["operationID"].astype(str).str.len()
df_om["operationID"] = df_om.apply(
    lambda x: "" if x["nb_digits"] < 20 else x.get("operationID", ""),
    axis=1
)


df_om['Amount']=df_om['debit']+df_om['credit']
df_om['Amount'] = df_om['Amount'].astype('float64')
df_om['technical_account']= "0" + df_om['technical_account'].astype(str)

list_initial = df_om['OMTransactionID'].to_list()



df_om_nan = df_om[(df_om["nb_digits"] < 20)]

df_om_ok = df_om[df_om["nb_digits"] == 20]


mapped_trx= df_om_ok["operationID"].to_list()

df_ams['Amount'] = df_ams['Amount'].astype('float64')
df_ams_nan = df_ams[~df_ams["operationID"].isin(mapped_trx)]

df_om_nan['TransactionDatetime'] = pd.to_datetime(
    df_om_nan['TransactionDatetime'], errors='coerce'
)
df_ams_nan['transactionDatetime'] = pd.to_datetime(
    df_ams_nan['transactionDatetime'], errors='coerce'
)


#{'0324820660', '0324820678', '0324820679', '0324820662'}
df_om_nan_repayment= df_om_nan[df_om_nan['technical_account'] == '0324820660' ]
df_om_nan_disbursement= df_om_nan[df_om_nan['technical_account'] == '0324820662' ]
df_om_nan_wtb= df_om_nan[df_om_nan['technical_account'] == '0324820678' ]
df_om_nan_btw= df_om_nan[df_om_nan['technical_account'] == '0324820679' ]


df_ams_nan_repayment= df_ams_nan[df_ams_nan['Type'] == 'CREDIT_REIMBURSEMENT' ]
df_ams_nan_disbursement= df_ams_nan[df_ams_nan['Type'] == 'CREDIT_REQUEST' ]
df_ams_nan_wtb= df_ams_nan[df_ams_nan['Type'] == 'SAVING_W2B' ]
df_ams_nan_btw= df_ams_nan[df_ams_nan['Type'] == 'SAVING_B2W' ]

#valid_types = ['repayment', 'B2W', 'W2B', 'disbursement']
#['IN', 'OUT']





df_repayment = getMatched(df_om_nan_repayment,df_ams_nan_repayment,direction='forward')
df_wtb = getMatched(df_om_nan_wtb,df_ams_nan_wtb,direction='forward')
df_disbursement = getMatched(df_om_nan_disbursement,df_ams_nan_disbursement,direction='backward')
df_btw = getMatched(df_om_nan_btw,df_ams_nan_btw,direction='backward')

df_reconciled = pd.concat([df_repayment,df_disbursement,df_wtb,df_btw])

col = ['N°', 'Date', 'Heure','OMTransactionID', 'Service', 'Statut', 'technical_account', 'debit',  'credit', 'TransactionDatetime', 'transaction_type','Amount', 'StatusAMS', 'StatusOM', 'RequestId', 'Type','operationID_om', 'operationID_ams', 'transactionDatetime',        'time_diff']
df_reconciled=df_reconciled[col]


df_reconciled = df_reconciled.rename(columns={'operationID_ams': 'operationID'})

]




col= ['Date', 'Heure', 'OMTransactionID', 'Service', 'Statut', 'technical_account', 'debit', 'credit', 'TransactionDatetime','transaction_type', 'operationID']

df_reconciled = df_reconciled[col]

df_om_ok_formated = df_om_ok[col]

df_result=pd.concat([df_reconciled,df_om_ok_formated])


    