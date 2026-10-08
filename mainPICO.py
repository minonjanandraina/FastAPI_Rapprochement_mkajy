# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 10:56:03 2025

@author: m.razakasoa
"""

import datetime
import calendar
import pandas as pd
import pico
import datetime



def ETL_PICO(d):
    filenamerepayment = f"Daily-Reimbursments_Pico-{d:%Y%m%d}.xls"
    filename_saving = f"Daily-Savings_Pico-{d:%Y%m%d}.xls"
    filename_credit= f"Daily-Credits_Pico-{d:%Y%m%d}.xls"
    
    try:
        df_pico_repayment = pico.get_pico_repayment_trx(filenamerepayment)
        print('')
    except Exception as e: 
        message = 'error while reading pico repayment file: {}'.format(e)
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx

    try:
        df_pico_saving = pico.get_pico_saving_trx(filename_saving)
    except Exception as e: 
        message = 'error while reading pico saving file: {}'.format(e)

        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx
        
    try:
        df_pico_disb = pico.get_pico_disbursement_trx(filename_credit)      
    except Exception as e: 
        message = 'error while reading pico credit file: {}'.format(e)
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': message
        }
        return ctx
    else:
        df_pico_repayment.to_excel(f"./staggingArea/PICO/dailyPICORepaymentTransaction-mkajy-{d:%Y%m%d}.xlsx")
        df_pico_saving.to_excel(f"./staggingArea/PICO/dailyPICOSavingTransaction-mkajy-{d:%Y%m%d}.xlsx")
        df_pico_disb.to_excel(f"./staggingArea/PICO/dailyPICODisbursementTransaction-mkajy-{d:%Y%m%d}.xlsx")
        ctx={
            'code':200,
            'Status': 'Success',
            'message': 'Data successfully loaded to ./staggingArea/PICO'
        }
        return ctx

    