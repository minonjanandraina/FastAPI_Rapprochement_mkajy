# -*- coding: utf-8 -*-
"""
Created on Tue Nov 25 11:25:52 2025

@author: m.razakasoa
"""

import pandas as pd
import urllib

from exceptions import dataInputEmpty,DatabaseError,dataCleanningError
from dotenv import load_dotenv
import os
import pyodbc
from tqdm import tqdm
import gc
from datetime import datetime, timedelta,date

import platform
import numpy as np
def pick_row(group):
    status3 = group[group["MerchantTransactionStatus"] == 3]
    
    if not status3.empty:
        return status3.sample(1)
    else:
        return group.sample(1)

def getCon():
    if platform.system() == 'Windows':
        driver = 'SQL Server'
    else:
        driver = 'ODBC Driver 17 for SQL Server'
    ip = '172.20.24.37'
    db_name= 'BIC'
    user_username = 'Minonja'
    user_password = 'Minonja'
    connection_string= 'DRIVER={driver};SERVER={ip};DATABASE={db_name};UID={user_name};PWD={user_password}'.format(driver=driver, ip=ip, db_name=db_name,user_name=user_username, user_password=user_password )
    print(connection_string)
    con  =pyodbc.connect(connection_string)    #to 
    return con




def getAMSTransaction(dateFrom,dateTo):
    dateFrom = dateFrom.strftime("%Y-%m-%d")
    dateTo = dateTo.strftime("%Y-%m-%d")

    con=getCon()
    sql="""
WITH vw_TransactionFront AS (
    SELECT  
        mc.apiLogId,
        mc.rMerchantId,
        mc.apiServiceId,
        mc.RequestId,

        ISNULL(rec.OmMongoId, mc.RequestId) AS OmMongoId,
        ISNULL(rec.StatusAMS, 'Not Mapped') AS StatusAMS,
        ISNULL(rec.StatusOM, 'Not Mapped') AS StatusOM,
        DATEADD(HOUR, 3, ISNULL(rec.TransactionDate, mc.ResponseDateCreated)) AS transactionDatetime,

        ty.Name AS rTransactionType,
        rec.Type,

        mc.rTransactionTypeID,
        mc.ReferenceAmountCRY,
        mc.rAutoTransactionID,
        mc.mcTransactionID,mc.Status
    FROM BIC.dbo.merchantTransaction mc
    JOIN CBS.dbo.rTransactionType ty
        ON ty.rTransactionTypeID = mc.rTransactionTypeID
    LEFT JOIN [bagsPAMF_CBS_INTG].dbo.AllReconciliatedItems rec
        ON rec.RequestId = mc.RequestId
    WHERE CONVERT(varchar, DATEADD(HOUR, 3, ISNULL(rec.TransactionDate, mc.ResponseDateCreated)), 23)
          BETWEEN '{dateFrom}' AND '{dateTo}'
      AND StatusOM = 'OK'
      AND RIGHT(rec.[RequestId], 10) != 'correction'
      
)

SELECT
    [StatusAMS],
    [StatusOM],
    [ReferenceAmountCRY] AS Amount,
    [RequestId],
    '' AS alias,
    '' AS uid_credit,
    [OmMongoId] AS operationID,
    transactionDatetime,
    '' AS YearMonth,
    mcTransactionID AS Id,
    ISNULL(
        [Type],
        CASE
            WHEN rTransactionType = 'Dépôt sur compte épargne' THEN 'SAVING_W2B'
            WHEN rTransactionType = 'Loan Activation | Principal | Wallet Disbursement' THEN 'CREDIT_REQUEST'
            WHEN rTransactionType = 'Retrait sur compte épargne' THEN 'SAVING_B2W'
            WHEN rTransactionType IN ('Transit | Merchant Loan Payment','Cash Over | Return Prepaid to Account from Loan') THEN 'CREDIT_REIMBURSEMENT'
        END
    ) AS [Type], status as MerchantTransactionStatus
FROM vw_TransactionFront;
    """.format(dateFrom=dateFrom,dateTo=dateTo)
    
    df_ams_INTG=pd.read_sql(sql, con)
    result = df_ams_INTG.groupby("RequestId", group_keys=False).apply(pick_row)

    return result

def getMappingAMS(d):

    con=getCon()
    
    sql="""
    select   distinct requestID as RequestId,OmMongoID as operationID
    
    from bic.dbo.allREconciliatedItems rec 
    
    where 
    
    year(DATEADD(hour,0,rec.TransactionDate))={year}
    and month(DATEADD(hour,0,rec.TransactionDate))={month}
    and day(DATEADD(hour,0,rec.TransactionDate))={day}
    """.format(year = d.year, month = d.month , day = d.day)
    print('*'*50)
    print(sql)
    print('*'*50)
    df_mapping_intg=pd.read_sql(sql, con)


    return df_mapping_intg

def getMatched(df_om,df_ams,direction='forward'):
    colom=['N°','Date','Heure','OMTransactionID','Service','Statut','technical_account','debit','credit','TransactionDatetime','transaction_type','operationID','nb_digits','Amount']
    
    df_om=df_om[colom]
    df_om_init=df_om.copy()
    df_om['TransactionDatetime'] = pd.to_datetime(
        df_om['TransactionDatetime'], errors='coerce'
    )
    df_om['TransactionDatetime'] = pd.to_datetime(df_om['TransactionDatetime'])

    df_ams['transactionDatetime'] = pd.to_datetime(
        df_ams['transactionDatetime'], errors='coerce'
    )
    df_ams['transactionDatetime'] = pd.to_datetime(df_ams['transactionDatetime'])

    df_reco=pd.DataFrame()
    len_rec=1
    # Filter where AMS transaction is within the time window (forward direction)
    list_used_OMTransactionID=[]
    list_used_operationID=[]
    while len_rec>0:
        print('----------------------------------------------------------')
        print(len_rec)
        print('----------------------------------------------------------')
        df_om = df_om[~df_om["OMTransactionID"].isin(list_used_OMTransactionID)]
        df_ams = df_ams[~df_ams["operationID"].isin(list_used_operationID)]
        reco_temp = df_om.merge(
            df_ams,
            on='Amount',
            how='inner',
            suffixes=('_om', '_ams')
        )
    
        
        
       # Calculate time difference
        if direction == 'forward':
            reco_temp = reco_temp[
                (reco_temp['transactionDatetime'] >= reco_temp['TransactionDatetime']) 
            ]
            reco_temp['time_diff'] = (
            reco_temp['transactionDatetime'] - reco_temp['TransactionDatetime']
            )
        elif direction == 'backward':
            reco_temp = reco_temp[
                ( reco_temp['TransactionDatetime']>= reco_temp['transactionDatetime'] ) 
            ]
            reco_temp['time_diff'] = (
            reco_temp['TransactionDatetime'] - reco_temp['transactionDatetime']
            )
               
        # Sort by time difference and keep the closest match for each OM transaction
        reco_temp = reco_temp.sort_values('time_diff').drop_duplicates(
            subset=['OMTransactionID'],  # or use a unique ID column if available
            keep='first'
        )
        
        reco_temp=reco_temp.drop_duplicates(subset=['OMTransactionID'],keep='first')
        len_rec=len(reco_temp)
        
        
        # Assuming df_reco (from matching) has these columns
        colrec = ['N°', 'Date', 'Heure', 'OMTransactionID', 'Service', 'Statut', 
          'technical_account', 'debit', 'credit', 'TransactionDatetime', 
          'transaction_type', 'operationID_om', 'nb_digits', 'Amount', 
          'StatusAMS', 'StatusOM', 'RequestId', 'alias', 'uid_credit', 
          'operationID_ams', 'transactionDatetime', 'YearMonth', 'Id', 
          'Type', 'time_diff']
        df_reco=pd.concat([df_reco,reco_temp])
        list_used_OMTransactionID=df_reco['OMTransactionID'].to_list()
        list_used_operationID=df_reco['operationID_ams'].to_list()
        print(df_reco.columns)
        # Left merge: keep all from df_om, add matching columns from df_reco
        df_result = df_om_init.merge(
            df_reco[['OMTransactionID', 'StatusAMS', 'StatusOM', 'RequestId', 'alias', 
                     'uid_credit', 'operationID_ams', 'transactionDatetime', 'YearMonth', 
                     'Id', 'Type', 'time_diff']],
            on='OMTransactionID',
            how='left'
        )
        
        # If you need to rename 'operationID' to 'operationID_om' to match colrec
        df_result = df_result.rename(columns={'operationID': 'operationID_om'})
        
        # Keep only the columns in colrec order
        df_result = df_result[colrec]
                
        return df_result

def checkMappedData(df_clean_OM_mapped,df_clean_OM):

    
    df_clean_OM_mapped['transactionAmount']= df_clean_OM_mapped['debit']+df_clean_OM_mapped['credit']
    
    df_clean_OM['transactionAmount']= df_clean_OM['debit']+df_clean_OM['credit']
    
    total_OM =df_clean_OM['transactionAmount'].sum()
    total_OM_mapped =df_clean_OM_mapped['transactionAmount'].sum()
    ecart = total_OM_mapped- total_OM
    if ecart > 0:
        raise dataCleanningError('Processing Error in mapped TransactionOM. Discrepencies = {}'.format(ecart))
        



