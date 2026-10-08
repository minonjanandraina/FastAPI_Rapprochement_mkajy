# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 09:34:45 2026

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
from datetime import datetime, timedelta



def getCon():
    load_dotenv()
    driver = os.getenv("env_driver")
    ip = os.getenv("ip")
    db_name= os.getenv("db_name")
    user_username = os.getenv('user_username')
    user_password = os.getenv('user_password')
    connection_string= 'DRIVER={driver};SERVER={ip};DATABASE={db_name};UID={user_name};PWD={user_password}'.format(driver=driver, ip=ip, db_name=db_name,user_name=user_username, user_password=user_password )
    print(connection_string)
    con  =pyodbc.connect(connection_string)    #to 
    return con



def generateGLTransaction(d):
    sql_gl="""
    
    SELECT 
    	   ga.[Code],
           ga.[Name],
           ggli.rAutoTransactionID,
           ggli.AmountCRY,
           ggli.DebitCredit ,
           gglid.Description, 
           ggli.rTransactionTypeID,ggli.PostingDate 
    FROM   cbs.dbo.glGeneralLedgerItem ggli
    JOIN cbs.dbo.glGeneralLedgerItemDescription gglid ON ggli.glGeneralLedgerItemID = gglid.glGeneralLedgerItemID
    JOIN cbs.dbo.glAccount ga ON ga.glAccountID = ggli.glaccountid
    
    where ga.Code in ('109000091','109000092','109000093','109000094')
    and ggli.PostingDate = '{date}'
    """.format(date=d)
    
    
    df_gl=pd.read_sql(sql_gl, getCon())
    filename_csv =  f"./output/GL/dailyGLTransaction-mkajy-{d:%Y-%m-%d}.csv"
    filename_xlsx =  f"./output/GL/dailyGLTransaction-mkajy-{d:%Y-%m-%d}.xlsx"
    df_gl.to_csv(filename_csv)
    df_gl.to_excel(filename_xlsx)
    ctx={
    "code": 200,
    "Status": "Success",
    "message": "GL Transaction Successfully cleanned"
    }
    return ctx
    


def generateFRONTTransaction(d):
    print('-------------------------------------------------------9999999999999999999')
    print(type(d))
    print('-------------------------------------------------------9999999999999999999')
    sql_front="""
    
    /****** Script de la commande SelectTopNRows à partir de SSMS  ******/
    SELECT
    	distinct
    	mc.[RequestId]
    
    	,mc.[rAutoTransactionID]
    
    	,mc.[ReferenceKey] as documentID
    	,mc.ReferenceAmountCRY as transactionAmount
    	,mc.RequestDateCreated
    	,mc.rTransactionTypeID
    	,mc.mcTransactionID
    	,mc.apiLogId
    
    FROM [BIC].[dbo].[merchantTransaction] mc
    
    
    where mc.[status]=3  
    
    and year(mc.[RequestDateCreated])={year}
    and month(mc.[RequestDateCreated])={month}
    and day(mc.[RequestDateCreated])={day}
    
    
    """.format(year = d.year, month = d.month , day = d.day)
    
    
    df_front=pd.read_sql(sql_front, getCon())
    
    filename_csv =  f"./output/FRONT/dailyFRONTTransaction-mkajy-{d:%Y-%m-%d}.csv"
    filename_xlsx =  f"./output/FRONT/dailyFRONTTransaction-mkajy-{d:%Y-%m-%d}.xlsx"
    df_front.to_csv(filename_csv)
    df_front.to_excel(filename_xlsx)
    ctx={
    "code": 200,
    "Status": "Success",
    "message": "FRONT Transaction Successfully cleanned"
    }
    return ctx