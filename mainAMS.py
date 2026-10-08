# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 16:39:01 2025

@author: m.razakasoa
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 16:34:38 2025

@author: m.razakasoa
"""
import datetime
import calendar
import pandas as pd
from util import getAMSTransaction
from datetime import date, timedelta,datetime


def ETL_AMS(d):
    df_ams =  getAMSTransaction( d  , d )
    df_ams = df_ams.drop_duplicates(subset=["RequestId"], keep="first")



    d_str = d.strftime("%Y%m%d")


    df_ams.to_excel(f"./staggingArea/PAMF/dailyPAMFTransaction-mkajy-{d_str}.xlsx")
    ctx={
        "code": 200,
        "Status": "success",
        "message": "PAMF Transaction Loaded"
    }
    return ctx