# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 15:48:14 2025

@author: m.razakasoa
"""

import datetime
import calendar
import pandas as pd


    
def ETL_OM(start):

    tangoFilename = f"./staggingArea/TANGO/DailyTangoTransaction-mkajy- {start:%Y%m%d}.xlsx"
    picoRepaymentFilename=f"./staggingArea/PICO/dailyPICORepaymentTransaction-mkajy-{start:%Y%m%d}.xlsx"
    picoSavingFilename=f"./staggingArea/PICO/dailyPICOSavingTransaction-mkajy-{start:%Y%m%d}.xlsx"
    picoDisbFilename=f"./staggingArea/PICO/dailyPICODisbursementTransaction-mkajy-{start:%Y%m%d}.xlsx"
    try:
        df_tango = pd.read_excel(tangoFilename)
    except Exception as e:
        message = 'error while reading clean tango file {file} file: {error}'.format(error= e,file=tangoFilename)
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx

    try:
        dfRepayment=pd.read_excel(picoRepaymentFilename)
  
    except Exception as e:
        message = 'error while reading clean PICO file {file} file: {error}'.format(error= e,file=picoRepaymentFilename)
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx
    try:
        dfSaving=pd.read_excel(picoSavingFilename)
  
    except Exception as e:
        message = 'error while reading clean PICO file {file} file: {error}'.format(error= e,file=picoSavingFilename)
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx
    try:
        dfDisb=pd.read_excel(picoDisbFilename)
  
    except Exception as e:
        message = 'error while reading clean PICO file {file} file: {error}'.format(error= e,file=picoDisbFilename)
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx

    col_mapping=['transaction_type','operationID','OMTransactionID']
    dfRepayment=dfRepayment[col_mapping]
    dfSaving=dfSaving[col_mapping]
    dfDisb=dfDisb[col_mapping]
    df_pico = pd.concat([dfRepayment,dfSaving,dfDisb], ignore_index=True)
    df_om=pd.merge(df_tango, df_pico, how='left', on='OMTransactionID' )
    if len(df_om) == 0 :
        ctx={
            'code':407,
            'Status': 'Failed',
            'message': 'Len of cleaned OM transaction can not be equal to 0'
        }
        return ctx
    else:
        
        df_om = df_om.drop_duplicates(subset=["OMTransactionID"], keep="first")
        df_om.to_excel(f"./staggingArea/OM/DailyOMTransaction-mkajy-{start:%Y%m%d}.xlsx")
        ctx={
            'code':200,
            'Status': 'Success',
            'message': 'Data successfully loaded to ./staggingArea/OM'
        }
        return ctx


