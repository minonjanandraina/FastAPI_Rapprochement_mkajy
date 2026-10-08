# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 10:56:16 2025

@author: m.razakasoa
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Nov 21 16:14:53 2025

@author: m.razakasoa
"""

import pandas as pd
import os

def get_pico_saving_trx(filename):
    path_saving = './input/PICO/SAVING/'
    file_path=path_saving+filename
    
    column_saving_pico=['No','partner_code','user_id','alias','vide','date_of_savings','transaction_type','Amount','savings_balance_after','operationID','operationStatus','failureReason','OMTransactionID','OM_transaction_tat']
    df_pico_saving_sheet = pd.read_excel(file_path, sheet_name=None, names=column_saving_pico, header=None)
    
    dataframes_saving = []

    # Parcourir chaque feuille et ajouter le nom de fichier à chaque DataFrame
    for sheet_name, df in df_pico_saving_sheet.items():  
        dataframes_saving.append(df)  # 
        print("Filename : " + filename + " sheet: " + sheet_name)
    df_pico_saving=pd.concat(dataframes_saving)
    
    df_pico_saving=df_pico_saving[df_pico_saving['operationStatus']=='OK']
    
    df_pico_saving=df_pico_saving[['transaction_type','operationID','OMTransactionID']]
    
    #df_pico_saving_b2w=df_pico_saving[df_pico_saving['transaction_type']=='B2W']
    #df_pico_saving_w2b=df_pico_saving[df_pico_saving['transaction_type']=='W2B']
    #ctx={'wtb':df_pico_saving_w2b,'btw':df_pico_saving_b2w}
    
    return df_pico_saving
def get_pico_repayment_trx(filename_pico_repayment):
    path_repayment ='./input/PICO/REPAYMENT/'
    print(path_repayment)
    print("REpayment folder is {}".format(path_repayment))
    
    
    
    file_full_path=path_repayment+filename_pico_repayment
    column_repayment_pico=['no','partner_code','user_id','alias','vide&','date_of_repayment','uid_credit','vide2','due_date','initialamount','Initiator','globaldue_before','Fees_before','vide','penalty_before','globaldue_after','fees_after','penalty_after','transaction_amount','transaction_amount_from_saving','status','operationID','OMTransactionID']
    # Charger toutes les feuilles sans header pour avoir un contrôle total
    df_pico_repayment_sheet = pd.read_excel(
        file_full_path,
        sheet_name=None,
        header=None
    )

    dataframes_repayment = []

    for idx, (sheet_name, df) in enumerate(df_pico_repayment_sheet.items()):
        if idx == 0:  
            # Première feuille → commencer à la ligne 20 (index 19 en zéro-based)
            df = pd.read_excel(
                file_full_path,
                sheet_name=sheet_name,
                names=column_repayment_pico,
                header=None,
                skiprows=19
            )
        else:
            # Les autres feuilles normalement
            df = pd.read_excel(
                file_full_path,
                sheet_name=sheet_name,
                names=column_repayment_pico,
                header=None
            )

        dataframes_repayment.append(df)
        print("Filename : " + filename_pico_repayment + " sheet: " + sheet_name)
    df_pico_repayment=pd.concat(dataframes_repayment)
    df_pico_repayment=df_pico_repayment[df_pico_repayment['transaction_amount']>0]
    df_pico_repayment['transaction_type']='repayment'
    df_pico_repayment=df_pico_repayment[['transaction_type','alias','uid_credit','operationID','OMTransactionID']]
    return df_pico_repayment
'''
def get_pico_disbursement_trx(file_pico_disbursement):
    path_disb = './input/PICO/CREDIT/'

    file_full_path = path_disb + file_pico_disbursement
    df_pico_disbursement_sheet = pd.read_excel(
        file_full_path,
        sheet_name=None,
        header=None
    )
    dataframes_disbursement = []

    column_disbursement_pico = ['partner_code', 'user_id', 'msisdn', 'alias', 'date_request', 'uidcredit', 'requested_amount', 'grantableamount', 'transaction_amount', 'operationID', 'operation_status', 'failure_reason', 'due_date', 'fees', 'OMTransactionID', 'status']

    for sheet_name, df in df_pico_disbursement_sheet.items():
        # Nouveau format : une seule colonne texte, valeurs séparées par '|', pas d'entête ni de bloc de métadonnées
        df = df[0].str.split('|', expand=True)
        df.columns = column_disbursement_pico

        dataframes_disbursement.append(df)
        print("Filename : " + file_pico_disbursement + " sheet: " + sheet_name)
    df_pico_disbursement = pd.concat(dataframes_disbursement)
    df_pico_disbursement = df_pico_disbursement[df_pico_disbursement['operation_status'] == 'OK']

    df_pico_disbursement['transaction_type'] = 'disbursement'
    df_pico_disbursement = df_pico_disbursement[['transaction_type', 'operationID', 'OMTransactionID']]
    return df_pico_disbursement
'''

def get_pico_disbursement_trx(file_pico_disbursement):
    path_disb = './input/PICO/CREDIT/'
    
    
    file_full_path=path_disb+file_pico_disbursement
    df_pico_disbursement_sheet = pd.read_excel(
        file_full_path,
        sheet_name=None,
        header=None
    )
    dataframes_disbursement = []

    column_disbursement_pico=['no','partner_code','user_id','alias','vide&','date_request','uidcredit','requested_amount','vide2','grantableamount','transaction_amount','operationID','operation_status','failure_reason','due_date','fees','OMTransactionID','status']
    for idx, (sheet_name, df) in enumerate(df_pico_disbursement_sheet.items()):
        if idx == 0:  
            # Première feuille → commencer à la ligne 20 (index 19 en zéro-based)
            df = pd.read_excel(
                file_full_path,
                sheet_name=sheet_name,
                names=column_disbursement_pico,
                header=None,
                skiprows=19
            )
        else:
            # Les autres feuilles normalement
            df = pd.read_excel(
                file_full_path,
                sheet_name=sheet_name,
                names=column_disbursement_pico,
                header=None
            )

        dataframes_disbursement.append(df)
        print("Filename : " + file_pico_disbursement + " sheet: " + sheet_name)
    df_pico_disbursement=pd.concat(dataframes_disbursement)
    df_pico_disbursement=df_pico_disbursement[df_pico_disbursement['operation_status']=='OK']

    df_pico_disbursement['transaction_type']='disbursement'
    df_pico_disbursement=df_pico_disbursement[['transaction_type','operationID','OMTransactionID']]
    return df_pico_disbursement