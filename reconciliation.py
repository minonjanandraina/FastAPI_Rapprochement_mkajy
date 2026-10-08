# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 11:00:25 2026

@author: m.razakasoa
"""
from sqlalchemy import create_engine, text
from datetime import datetime, date
import pandas as pd

engine = create_engine(
    "mssql+pyodbc://Minonja:Minonja@172.20.24.37/RECONCILIATION_DFS?driver=SQL+Server"
)


def reconcile_transactions(df_ams, df_om, max_time_diff_minutes=60):

    TYPE_MAPPING = {
        'CREDIT_REIMBURSEMENT': ['repayment', 'wallet_to_bank'],
        'REPAYMENT':            ['repayment', 'wallet_to_bank'],
        'CREDIT_REQUEST':       ['disbursement'],
        'DISBURSEMENT':         ['disbursement'],
        'SAVING_B2W':           ['bank_to_wallet'],
        'BANK_TO_WALLET':       ['bank_to_wallet'],
        'SAVING_W2B':           ['wallet_to_bank'],
        'WALLET_TO_BANK':       ['wallet_to_bank'],
    }

    df_ams = df_ams.copy()
    df_om  = df_om.copy()

    df_ams['matched'] = False
    df_om['matched']  = False

    matches   = []
    ambiguous = []

    TARGET_OM  = 'CO260121.1953.A99820'
    TARGET_AMS = 'PCMG0121165336807wnY'

    for i, ams in df_ams.iterrows():

        is_target_ams = (ams['operationID'] == TARGET_AMS)

        ams_type         = ams.get('Type', None)
        allowed_om_types = TYPE_MAPPING.get(ams_type, None)

        if is_target_ams:
            print("\n" + "="*60)
            print("[TARGET AMS] operationID : {}".format(ams['operationID']))
            print("             Type        : {}".format(repr(ams_type)))
            print("             Amount      : {}".format(repr(ams['Amount'])))
            print("             datetime    : {}".format(ams['transactionDatetime']))
            print("             allowed_om  : {}".format(allowed_om_types))

        # -- step 1: amount + unmatched filter
        candidates = df_om[
            (df_om['matched'] == False) &
            (abs(df_om['credit'] - ams['Amount']) < 0.001)
        ].copy()

        if is_target_ams:
            print("\n[STEP 1] candidates after amount filter : {}".format(len(candidates)))
            if TARGET_OM in df_om['OMTransactionID'].values:
                om_row = df_om[df_om['OMTransactionID'] == TARGET_OM].iloc[0]
                print("         TARGET_OM matched flag : {}".format(om_row['matched']))
                print("         TARGET_OM credit       : {}".format(repr(om_row['credit'])))
                print("         amount diff            : {}".format(abs(om_row['credit'] - ams['Amount'])))
                print("         TARGET_OM in candidates: {}".format(TARGET_OM in candidates['OMTransactionID'].values))

        if len(candidates) == 0:
            if is_target_ams:
                print("[STEP 1] STOPPED - no candidates after amount filter")
            continue

        # -- step 2: type filter
        if allowed_om_types is not None:
            candidates = candidates[
                candidates['transaction_type'].isin(allowed_om_types)
            ]

        if is_target_ams:
            print("\n[STEP 2] candidates after type filter   : {}".format(len(candidates)))
            if TARGET_OM in df_om['OMTransactionID'].values:
                om_row = df_om[df_om['OMTransactionID'] == TARGET_OM].iloc[0]
                print("         TARGET_OM transaction_type : {}".format(repr(om_row['transaction_type'])))
                print("         TARGET_OM in candidates   : {}".format(TARGET_OM in candidates['OMTransactionID'].values))

        if len(candidates) == 0:
            if is_target_ams:
                print("[STEP 2] STOPPED - no candidates after type filter")
            continue

        # -- step 3: time diff filter
        candidates['time_diff'] = (
            abs((candidates['TransactionDatetime'] - ams['transactionDatetime'])
                .dt.total_seconds()) / 60
        )

        if is_target_ams:
            print("\n[STEP 3] time diffs (minutes):")
            print(candidates[['OMTransactionID', 'TransactionDatetime', 'transaction_type', 'time_diff']])
            if TARGET_OM in candidates['OMTransactionID'].values:
                td = candidates[candidates['OMTransactionID'] == TARGET_OM]['time_diff'].iloc[0]
                print("         TARGET_OM time_diff : {} min  (limit={})".format(td, max_time_diff_minutes))

        candidates = candidates[candidates['time_diff'] <= max_time_diff_minutes]

        if is_target_ams:
            print("\n[STEP 3] candidates after time filter   : {}".format(len(candidates)))
            print("         TARGET_OM in candidates        : {}".format(TARGET_OM in candidates['OMTransactionID'].values))

        if len(candidates) == 0:
            if is_target_ams:
                print("[STEP 3] STOPPED - no candidates after time filter")
            continue

        # -- step 4: score + best pick
        candidates['score'] = 100 - candidates['time_diff']
        best = candidates.sort_values('score', ascending=False).iloc[0]
        j    = best.name

        if is_target_ams:
            print("\n[STEP 4] MATCHED with OMTransactionID : {}".format(df_om.loc[j, 'OMTransactionID']))

        df_ams.at[i, 'matched'] = True
        df_om.at[j,  'matched'] = True

        matches.append({
            "operationID":       ams['operationID'],
            "OMTransactionID":   df_om.loc[j, 'OMTransactionID'],
            "ams_type":          ams_type,
            "om_type":           df_om.loc[j, 'transaction_type'],
            "time_diff_min":     best['time_diff'],
            "match_probability": best['score'],
            "status":            "MATCHED"
        })

        if len(candidates) > 1:
            ambiguous.append({
                "operationID":      ams['operationID'],
                "possible_matches": list(candidates['OMTransactionID'])
            })

    if TARGET_AMS not in df_ams['operationID'].values:
        print("\nWARNING: TARGET_AMS '{}' was NOT present in df_ams at all!".format(TARGET_AMS))
    if TARGET_OM not in df_om['OMTransactionID'].values:
        print("\nWARNING: TARGET_OM '{}' was NOT present in df_om at all!".format(TARGET_OM))

    return {
        "matches":       pd.DataFrame(matches),
        "remaining_ams": df_ams[df_ams['matched'] == False],
        "remaining_om":  df_om[df_om['matched'] == False],
        "ambiguous":     pd.DataFrame(ambiguous)
    }

def checkUnprocessed(merchantTransactionStatus, currentStatus):
    try:
        if int(merchantTransactionStatus) != 3:
            return 'UNPROCESSED'
        return currentStatus
    except (ValueError, TypeError):
        return currentStatus


def main(d):
    dt = d.strftime("%Y%m%d")

    filename_om             = f"./staggingArea/OM/DailyOMTransaction-mkajy-{dt}.xlsx"
    filename_ams            = f"./staggingArea/PAMF/dailyPAMFTransaction-mkajy-{dt}.xlsx"
    filename_reconcile_om   = f"./output/reconciliation/dailyTransaction-reconciliation-OM-{dt}.xlsx"
    filename_reconcile_ams  = f"./output/reconciliation/dailyTransaction-reconciliation-AMS-{dt}.xlsx"
    filename_duplicated_ams = f"./output/reconciliation/dailyTransaction-duplicated-ams-{dt}.xlsx"

    # -- read source files ------------------------------------------------------
    df_om = pd.read_excel(filename_om, usecols=range(2, 14), dtype={'technical_account': str})

    # clean scientific notation leftover (e.g. '3.25E+08' -> '324820679')
    df_om['technical_account'] = df_om['technical_account'].apply(
        lambda x: str(int(float(x))) if pd.notna(x) else x
    )
    
    # regenerate transaction_type from technical_account
    TECHNICAL_ACCOUNT_TYPE_MAPPING = {
        '324820660': 'repayment',
        '324820662': 'disbursement',
        '324820678': 'wallet_to_bank',
        '324820679': 'bank_to_wallet',
    }
    df_om['transaction_type'] = df_om['technical_account'].map(TECHNICAL_ACCOUNT_TYPE_MAPPING)

    df_ams = pd.read_excel(filename_ams, usecols=range(1, 13))
    # When reading files, strip and normalize
    df_ams['Type'] = df_ams['Type'].str.strip()
    df_om['transaction_type'] = df_om['transaction_type'].str.strip()
    
    df_om['credit']            = pd.to_numeric(df_om['credit'],  errors='coerce')
    df_ams['Amount']           = pd.to_numeric(df_ams['Amount'], errors='coerce')
    df_ams['Type']             = df_ams['Type'].str.strip().str.upper()
    df_om['transaction_type']  = df_om['transaction_type'].str.strip().str.lower()
    # -- handle duplicates in AMS -----------------------------------------------
    df_ams['is_duplicate'] = df_ams.duplicated(subset=['operationID'], keep=False)
    df_ams_duplicated = df_ams[df_ams['is_duplicate']]
    df_ams = df_ams.drop_duplicates(subset=['operationID', 'Amount'], keep='first')

    # -- exact match on operationID (inner join) --------------------------------
    df_combined = pd.merge(df_om, df_ams, how='inner', on='operationID')

    # -- split into "both" and "only" sets -------------------------------------
    df_om_only  = df_om [~df_om ['OMTransactionID'].isin(df_combined['OMTransactionID'])].copy()
    df_ams_only = df_ams[~df_ams['operationID']    .isin(df_combined['operationID'])    ].copy()

    df_om_only  = df_om_only [df_om .columns]
    df_ams_only = df_ams_only[df_ams.columns]

    df_om_both  = df_om [df_om ['OMTransactionID'].isin(df_combined['OMTransactionID'])].copy()
    df_ams_both = df_ams[df_ams['operationID']    .isin(df_combined['operationID'])    ].copy()

    df_om_both  = df_om_both [df_om .columns]
    df_ams_both = df_ams_both[df_ams.columns]

    # -- cross-populate for EXACT MATCHING rows ---------------------------------
    # df_om_both  gets RequestId       from df_ams_both (via operationID)
    # df_ams_both gets OMTransactionID from df_om_both  (via operationID)
    df_om_both = pd.merge(
        df_om_both,
        df_ams_both[['operationID', 'RequestId']],
        on='operationID', how='left'
    )
    df_ams_both = pd.merge(
        df_ams_both,
        df_om_both[['operationID', 'OMTransactionID']],
        on='operationID', how='left'
    )

    df_om_both['time_diff_min']     = 0
    df_om_both['match_probability'] = 100
    df_om_both['status']            = 'EXACT MATCHING'

    df_ams_both['time_diff_min']     = 0
    df_ams_both['match_probability'] = 100
    df_ams_both['status']            = 'EXACT MATCHING'

    # -- sort before fuzzy reconciliation --------------------------------------
    df_om_only  = df_om_only .sort_values(by='OMTransactionID')
    df_ams_only = df_ams_only.sort_values(by='transactionDatetime')

    result      = reconcile_transactions(df_ams_only, df_om_only, max_time_diff_minutes=60)
    df_matching = result['matches']

    if len(df_matching) > 0:

        # ? enrich df_matching with RequestId right away, while operationID is known
        df_matching = pd.merge(
            df_matching,
            df_ams[['operationID', 'RequestId']],
            on='operationID', how='left'
        )

        df_remaining_ams = result['remaining_ams'].copy()
        df_remaining_om  = result['remaining_om'] .copy()

        # -- ORPHAN rows --------------------------------------------------------
        df_remaining_om['RequestId']         = None
        df_remaining_om['OMTransactionID']   = df_remaining_om['OMTransactionID']  # already present
        df_remaining_om['time_diff_min']     = 0
        df_remaining_om['match_probability'] = 0
        df_remaining_om['status']            = 'ORPHAN'

        df_remaining_ams['OMTransactionID']  = None
        df_remaining_ams['time_diff_min']    = 0
        df_remaining_ams['match_probability']= 0
        df_remaining_ams['status']           = 'ORPHAN'

        # -- fuzzy-matched OM rows ----------------------------------------------
        # RequestId is now carried inside df_matching — no second join needed
        df_om_only = pd.merge(
            df_om_only,
            df_matching[['OMTransactionID', 'operationID', 'RequestId',
                         'time_diff_min', 'match_probability', 'status']],
            on='OMTransactionID', how='inner'
        )
        df_om_only = df_om_only.drop('operationID_x', axis=1, errors='ignore')
        df_om_only = df_om_only.rename(columns={'operationID_y': 'operationID'})

        # -- fuzzy-matched AMS rows ---------------------------------------------
        df_ams_only = pd.merge(
            df_ams_only,
            df_matching[['operationID', 'OMTransactionID',
                         'time_diff_min', 'match_probability', 'status']],
            on='operationID', how='inner'
        )

        # -- align columns before concat ----------------------------------------
        om_cols  = list(df_om_both.columns)
        ams_cols = list(df_ams_both.columns)

        df_om_only      = df_om_only     [om_cols]
        df_remaining_om = df_remaining_om[om_cols]

        df_ams_only      = df_ams_only     [ams_cols]
        df_remaining_ams = df_remaining_ams[ams_cols]

        df_finale_om  = pd.concat([df_om_both,  df_om_only,  df_remaining_om ], ignore_index=True)
        df_finale_ams = pd.concat([df_ams_both, df_ams_only, df_remaining_ams], ignore_index=True)

    else:
        # no fuzzy matches — df_om_only and df_ams_only are all orphans
        df_om_only['RequestId']        = None   # no AMS counterpart
        df_ams_only['OMTransactionID'] = None   # no OM counterpart

        df_om_only['time_diff_min']     = 0
        df_om_only['match_probability'] = 0
        df_om_only['status']            = 'ORPHAN'

        df_ams_only['time_diff_min']     = 0
        df_ams_only['match_probability'] = 0
        df_ams_only['status']            = 'ORPHAN'

        df_finale_om  = pd.concat([df_om_both,  df_om_only ], ignore_index=True)
        df_finale_ams = pd.concat([df_ams_both, df_ams_only], ignore_index=True)

    # -- save duplicates --------------------------------------------------------
    df_ams_duplicated.to_excel(filename_duplicated_ams)

    print('-' * 50)
    print(df_finale_om.columns)
    print(df_finale_ams.columns)
    print('-' * 50)

    # -- attach MerchantTransactionStatus to OM for auditing -------------------
    df_finale_om = pd.merge(
        df_finale_om,
        df_finale_ams[['operationID', 'MerchantTransactionStatus']],
        on='operationID', how='left'
    )

    # -- apply UNPROCESSED check on AMS side -----------------------------------
    df_finale_ams['status'] = df_finale_ams.apply(
        lambda row: checkUnprocessed(row['MerchantTransactionStatus'], row['status']), axis=1
    )

    print('45' * 50)
    print(df_finale_om.columns)
    print(df_finale_ams.columns)
    print('45' * 50)

    df_finale_om .to_excel(filename_reconcile_om)
    df_finale_ams.to_excel(filename_reconcile_ams)

    return {
        "code":    200,
        "Status":  "success",
        "message": "Reconciliation Transaction Loaded"
    }


if __name__ == "__main__":

    list_date = [
        date(2026, 3,  1), date(2026, 3,  2), date(2026, 3,  3),
        date(2026, 3,  4), date(2026, 3,  5), date(2026, 3,  6),
        date(2026, 3,  7), date(2026, 3,  8), date(2026, 3,  9),
        date(2026, 3, 10), date(2026, 3, 11), date(2026, 3, 12),
        date(2026, 3, 13), date(2026, 3, 14), date(2026, 3, 15),
    ]

    for d in list_date:
        main(d)