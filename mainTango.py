# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 10:17:40 2025

@author: m.razakasoa

this script is used to generate clean and accurate Tango Transaction, plitted to transaction type by technical account, rollbacked and manualTransactions
"""

import tango 


import pandas as pd
from datetime import datetime, timedelta


start = datetime(2025,12, 7)

def ETL_TANGO(start):

    filename_tango = f"Daily-ChannelUserTransactionReport-0324820695-{start:%Y%m%d}.xls"
    print("Getting Tango Transactions...")
    try:
        dic_tango=tango.get_tango_transaction(filename_tango)
        dic_tango_clean=tango.cleanTangoTransaction(dic_tango)
    except RuntimeError as r:
        ctx={
            'code':401,
            'Status': 'Failed',
            'message': 'RuntimeError : {}'.format(r)
        }
        return ctx
    except ValueError as v:
        ctx={
            'code':402,
            'Status': 'Failed',
            'message': 'ValueError : {}'.format(v)
        }
        return ctx
    except FileNotFoundError as f:
        ctx={
            'code':403,
            'Status': 'Failed',
            'message': 'FileNotFoundError : {}'.format(f)
        }
        return ctx
    except KeyError as ke:
        ctx={
            'code':404,
            'Status': 'Failed',
            'message': 'KeyError : {}'.format(ke)
        }
        return ctx
    except Exception as e:
        ctx={
            'code':500,
            'Status': 'Failed',
            'message': 'Expected error : {}'.format(e)
        }
        return ctx
        
    try:#check data accuracy
        tango.raiseAccuracyErrorIfExist(dic_tango,dic_tango_clean)
        tango.raiseCleanningError(dic_tango,dic_tango_clean)
    except Exception as e:
        ctx={
            'code':409,
            'Status': 'Failed',
            'message': 'Data accuracy error : {}'.format(e)
        }
        return ctx
    try:
        df_repayment = dic_tango_clean['repayment']
        df_deposit = dic_tango_clean['deposit']
        df_withdrawal = dic_tango_clean['withdrawal']
        df_disbursement = dic_tango_clean['disbursment']
        df_manual = dic_tango_clean['manualTransaction']
        df_rollback = dic_tango_clean['rollback']
    except Exception as e:
        ctx={
            'code':408,
            'Status': 'Failed',
            'message': 'Tango data split error : {}'.format(e)
        }
        return ctx
    else:
        df_tangoFinale = pd.concat([df_repayment,df_deposit,df_withdrawal,df_disbursement],ignore_index=True)
        df_tangoFinale.to_excel(f"./staggingArea/TANGO/DailyTangoTransaction-mkajy- {start:%Y%m%d}.xlsx")
        df_manual.to_excel(f"./staggingArea/TANGO/DailyTangoTransaction-manual- {start:%Y%m%d}.xlsx")
        df_rollback.to_excel(f"./staggingArea/TANGO/DailyTangoTransaction-rollback- {start:%Y%m%d}.xlsx")
        ctx={
            'code':200,
            'Status': 'Success',
            'message': 'Data successfully loaded to ./staggingArea/TANGO'
        }
        return ctx
