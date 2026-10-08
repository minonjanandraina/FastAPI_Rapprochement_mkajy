# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 10:34:01 2025

@author: m.razakasoa
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 10:33:31 2025

@author: m.razakasoa
"""
from exceptions import dataCleanningError
from dotenv import load_dotenv
import pandas as pd
import os


def reading_tango_file(filename):
    try:
        print("####### Reading Tango files")
        
        # Load environment variables
        try:
            load_dotenv()
        except Exception as e:
            raise RuntimeError(f"Failed to load .env file: {e}")
        
        tech_account_list = ['0324820660','0324820662','0324820678','0324820679']
        col = ['N°','Date','Heure','OMTransactionID','Service','Paiement','Statut','Mode',
               'technical_account','Wallet','N° Pseudo','N° de Compte Client','Wallet','debit','credit',
               'Compte: 0324820695','Sous-réseau']

        # Get path from environment
        path_tango = './input/TANGO/'
        if not path_tango:
            raise ValueError("Environment variable 'path_tangoDaily' is not set")

        file_path = os.path.join(path_tango, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Tango file not found: {file_path}")
        print(file_path)

        # Read Excel file
        try:
            all_sheets = pd.read_excel(file_path, sheet_name=None, names=col, header=None,
                                       dtype={"technical_account": str})
        except ValueError as e:
            raise ValueError(f"Error reading Excel file: {e}")
        except Exception as e:
            raise RuntimeError(f"Unknown error reading Excel file: {e}")

        # Concatenate sheets
        dataframes = []
        for sheet_name, df in all_sheets.items():
            if df.empty:
                print(f"Warning: Sheet {sheet_name} is empty")
            dataframes.append(df)
            print(f"Filename: {filename} sheet: {sheet_name}")

        try:
            df_tango = pd.concat(dataframes, ignore_index=True)
        except ValueError as e:
            raise ValueError(f"Error concatenating sheets: {e}")

        # Filter by 'Statut'
        if 'Statut' not in df_tango.columns:
            raise KeyError("'Statut' column is missing in Tango file")
        df_tango = df_tango[df_tango['Statut'] == 'Succès']

        # Filter by technical accounts
        if 'technical_account' not in df_tango.columns:
            raise KeyError("'technical_account' column is missing in Tango file")
        df_tango = df_tango[df_tango['technical_account'].isin(tech_account_list)]

        # Keep only required columns
        required_columns = ['N°', 'Date', 'Heure', 'OMTransactionID', 'Service', 'Statut', 'technical_account', 'debit', 'credit']
        for col_name in required_columns:
            if col_name not in df_tango.columns:
                raise KeyError(f"Required column '{col_name}' is missing")
        df_tango = df_tango[required_columns]

        # Fill NaN values
        df_tango['debit'] = df_tango['debit'].fillna(0)
        df_tango['credit'] = df_tango['credit'].fillna(0)

        # Create datetime
        try:
            df_tango['TransactionDatetime'] = pd.to_datetime(df_tango['Date'] + ' ' + df_tango['Heure'], dayfirst=True)
        except Exception as e:
            raise ValueError(f"Error converting to datetime: {e}")

        print("####### Reading Tango files... Done")

        # Separate normal and manual transactions
        list_service_manual_trx = ['C2C Transfer', 'Transaction Correction', 'Operator Withdraw', 'O2C Transfer']
        df_tango_normale = df_tango[~df_tango["Service"].isin(list_service_manual_trx)]
        df_tango_manual = df_tango[df_tango["Service"].isin(list_service_manual_trx)]

        return df_tango_normale, df_tango_manual

    except Exception as e:
        print(f"[ERROR] reading_tango_file failed: {e}")
        raise
def split_tango_transaction(df):

    DF_tango_repayment=df[df['technical_account']=='0324820660']
    DF_tango_disbursement=df[df['technical_account']=='0324820662']
    DF_tango_deposit=df[df['technical_account']=='0324820678']
    DF_tango_withdrawal=df[df['technical_account']=='0324820679']
    

    cxt={
        'repayment':DF_tango_repayment,
        'disbursment':DF_tango_disbursement,
        'deposit':DF_tango_deposit,
        'withdrawal':DF_tango_withdrawal,
        }
    return cxt

def get_tango_transaction(file_name):
    DF_tango,DF_tango_manual=reading_tango_file(file_name)
    dict_tangoDF = split_tango_transaction(DF_tango)
    dict_tangoDF['manualTransaction']=DF_tango_manual
    return dict_tangoDF

def find_rollbacked(df_tango, max_delta_seconds=10):

    # Split IN / OUT
    df_in  = df_tango[df_tango['Service'] == 'Cash in'].copy()
    df_out = df_tango[df_tango['Service'] == 'Cash Out'].copy()

    # Keep only out rows that match amounts from in rows
    matching_amounts = set(df_in['debit'])
    df_out = df_out[df_out['credit'].isin(matching_amounts)].copy()

    # Prepare columns for merge
    df_in = df_in.rename(columns={'OMTransactionID': 'ref_in'})
    df_out = df_out.rename(columns={'OMTransactionID': 'ref_out'})

    # Merge on amount and technical_account
    merged = pd.merge(
        df_in,
        df_out,
        left_on=['debit', 'technical_account'],
        right_on=['credit', 'technical_account'],
        suffixes=('_in', '_out')
    )

    # Compute time delta (IN - OUT)
    merged['delta'] = (merged['TransactionDatetime_in'] -
                       merged['TransactionDatetime_out']).dt.total_seconds()

    # Keep only valid deltas
    merged = merged[(merged['delta'] >= 0) & (merged['delta'] <= max_delta_seconds)]

    if merged.empty:
        return []

    # Keep the best (smallest delta) OUT row per IN row
    merged = merged.sort_values('delta').drop_duplicates(subset=['ref_in'], keep='first')

    # Avoid duplicate OUT transactions (one-to-one matching)
    merged = merged.sort_values('delta').drop_duplicates(subset=['ref_out'], keep='first')

    # Produce flat list [ref_in, ref_out, ref_in, ref_out, ...]
    result = []
    for _, row in merged.iterrows():
        result.append(row['ref_in'])
        result.append(row['ref_out'])
    return result


def cleanTangoTransaction(Dic_tango):

    DF_tango_deposit=Dic_tango['deposit']
    DF_tango_repayment=Dic_tango['repayment']

    
    DF_tango_withdrawal_real=Dic_tango['withdrawal']
    DF_tango_disbursment_real=Dic_tango['disbursment']
    DF_tango_manual=Dic_tango['manualTransaction']
    
    list_rollbacked_repayment  = find_rollbacked(DF_tango_repayment,max_delta_seconds=10)
    list_rollbacked_deposit  = find_rollbacked(DF_tango_deposit,max_delta_seconds=10)#max_delta_seconds = distance maximum entre une transaction et sa correction en cas d'echec
    
    DF_tango_repayment_real = DF_tango_repayment[~DF_tango_repayment["OMTransactionID"].isin(list_rollbacked_repayment)]
    DF_tango_deposit_real = DF_tango_deposit[~DF_tango_deposit["OMTransactionID"].isin(list_rollbacked_deposit)]

    DF_tango_repayment_rollback = DF_tango_repayment[DF_tango_repayment["OMTransactionID"].isin(list_rollbacked_repayment)]
    DF_tango_deposit_rollback = DF_tango_deposit[DF_tango_deposit["OMTransactionID"].isin(list_rollbacked_deposit)]
    
    DF_tango_rollback = pd.concat([DF_tango_repayment_rollback, DF_tango_deposit_rollback, ], ignore_index=True)
    
    df_tango_clean={         
                       'deposit': DF_tango_deposit_real,
                       'repayment': DF_tango_repayment_real,
                       'withdrawal': DF_tango_withdrawal_real,
                       'disbursment': DF_tango_disbursment_real,
                       'rollback': DF_tango_rollback,
                       'manualTransaction': DF_tango_manual
                       
            }
    return df_tango_clean

def raiseAccuracyErrorIfExist(dic_tango,dic_tango_clean):
    transaction_init_repayment = dic_tango['repayment']['credit'].sum() -dic_tango['repayment']['debit'].sum() 
    transaction_cleaned_repayment = dic_tango_clean['repayment']['credit'].sum() -dic_tango_clean['repayment']['debit'].sum()
    
    transaction_init_disbursment = dic_tango['disbursment']['credit'].sum() -dic_tango['disbursment']['debit'].sum() 
    transaction_cleaned_disbursment = dic_tango_clean['disbursment']['credit'].sum() -dic_tango_clean['disbursment']['debit'].sum()
    
    transaction_init_deposit = dic_tango['deposit']['credit'].sum() -dic_tango['deposit']['debit'].sum() 
    transaction_cleaned_deposit= dic_tango_clean['deposit']['credit'].sum() -dic_tango_clean['deposit']['debit'].sum()
    
    transaction_init_withdrawal = dic_tango['withdrawal']['credit'].sum() -dic_tango['withdrawal']['debit'].sum() 
    transaction_cleaned_withdrawal= dic_tango_clean['withdrawal']['credit'].sum() -dic_tango_clean['withdrawal']['debit'].sum()
    
    
    #Check if data cleaning does not lost data
    if  transaction_init_repayment - transaction_cleaned_repayment >0:
        lost = transaction_init_repayment - transaction_cleaned_repayment
        raise dataCleanningError('data cleaning error for repayment transactions. initial transaction = {i}, cleaned = {c}-- lost transaction = {l})'.format(i=transaction_init_repayment,c=transaction_cleaned_repayment, l=lost))
        
    if  transaction_init_disbursment - transaction_cleaned_disbursment >0:
        lost = transaction_init_disbursment - transaction_cleaned_disbursment
        raise dataCleanningError('data cleaning error for disbursment transactions. initial transaction = {i}, cleaned = {c}-- lost transaction = {l})'.format(i=transaction_init_disbursment,c=transaction_cleaned_disbursment, l=lost))
        
    if  transaction_init_deposit - transaction_cleaned_deposit >0:
        lost = transaction_init_deposit - transaction_cleaned_deposit
        raise dataCleanningError('data cleaning error for deposit transactions. initial transaction = {i}, cleaned = {c}-- lost transaction = {l})'.format(i=transaction_init_deposit,c=transaction_cleaned_deposit, l=lost))
        
    if  transaction_init_withdrawal - transaction_cleaned_withdrawal >0:
        lost = transaction_init_withdrawal - transaction_cleaned_withdrawal
        raise dataCleanningError('data cleaning error for withdrawal transactions. initial transaction = {i}, cleaned = {c}-- lost transaction = {l})'.format(i=transaction_init_withdrawal,c=transaction_cleaned_withdrawal, l=lost))
    
    #Check if data is clean or not
def raiseCleanningError(dic_tango,dic_tango_clean):
    if dic_tango_clean['repayment']['debit'].sum()>0:
        df=dic_tango_clean['repayment']
        df=df[df['debit']>0]
        list_dirty = df['OMTransactionID'].to_list()
        list_dirty = ", ".join(list_dirty)  
        raise dataCleanningError('Dirty Data: Debit repayment amount: {}. list = [{}]'.format(dic_tango_clean['repayment']['debit'].sum(),list_dirty))
        
    if dic_tango_clean['deposit']['debit'].sum()>0:
        raise dataCleanningError('Dirty Data: Debit deposit amount: {}'.format(dic_tango_clean['deposit']['debit'].sum()))
    
    if dic_tango_clean['disbursment']['credit'].sum()>0:
        df=dic_tango_clean['disbursment']
        df=df[df['credit']>0]
        list_dirty = df['OMTransactionID'].to_list()
        list_dirty = ", ".join(list_dirty) 
        raise dataCleanningError('Dirty Data: credit disbursment amount: {} . list = [{}]'.format(dic_tango_clean['disbursment']['credit'].sum(),list_dirty))
        
    if dic_tango_clean['withdrawal']['credit'].sum()>0:
        df=dic_tango_clean['withdrawal']
        df=df[df['credit']>0]
        list_dirty = df['OMTransactionID'].to_list()
        list_dirty = ", ".join(list_dirty) 
        raise dataCleanningError('Dirty Data: credit withdrawal amount: {} . list = [{}]'.format(dic_tango_clean['withdrawal']['credit'].sum(),list_dirty))
        