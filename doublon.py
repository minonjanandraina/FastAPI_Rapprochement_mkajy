# -*- coding: utf-8 -*-
"""
Détection de transactions doublons (J-1) et envoi de rapport par mail.
Exécution quotidienne planifiée (cron / Task Scheduler).
"""

import platform
import smtplib
from datetime import date, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO

import pandas as pd
import pyodbc


# ─────────────────────────────────────────────
# 1. CONNEXION
# ─────────────────────────────────────────────

def get_connection():
    driver = 'SQL Server' if platform.system() == 'Windows' else 'ODBC Driver 17 for SQL Server'
    connection_string = (
        "DRIVER={{{driver}}};SERVER={ip};DATABASE={db};"
        "UID={user};PWD={pwd}"
    ).format(
        driver=driver,
        ip='172.20.24.37',
        db='BIC',
        user='Minonja',
        pwd='Minonja',
    )
    return pyodbc.connect(connection_string)


# ─────────────────────────────────────────────
# 2. QUERY OPTIMISÉE  (filtre J-1 dynamique)
# ─────────────────────────────────────────────
# Gains vs version initiale :
#   • CAST(PostingDate AS DATE) = @date  →  index seek possible (pas de fonction sur colonne)
#   • HAVING count > 1                   →  seuls les vrais doublons remontent
#   • Suppression de year()              →  évite le full-scan
# ─────────────────────────────────────────────

QUERY = """
SELECT
    l.requestID,
    COUNT(mc.mcTransactionID)  AS nb,
    SUM(mc.amountCRY)          AS amount
FROM [bagsPAMF_CBS_MC].[dbo].apiLog          l
JOIN cbs.dbo.mcTransaction                   mc  ON mc.RequestID = l.apiLogId
WHERE
    mc.Status        = 3
    AND l.apiServiceId  IN (700, 701, 302)
    AND CAST(mc.PostingDate AS DATE) = CAST(? AS DATE)   -- paramètre J-1
GROUP BY
    l.requestID
HAVING
    COUNT(mc.mcTransactionID) > 1            -- doublons uniquement
ORDER BY
    nb DESC, amount DESC;
"""


# ─────────────────────────────────────────────
# 3. ENVOI MAIL
# ─────────────────────────────────────────────

def send_report(posting_date: date, df_duplicates: pd.DataFrame) -> None:
    sender     = "no-reply@pamf.mg"
    recipients = [
        'm.razakasoa@pamf.mg',
        'n.ramiaramananjafy@pamf.mg',
        'd.ravalison@pamf.mg',
        'k.rabenja@pamf.mg',
        'a.ralantoharivelo@pamf.mg'
    ]
    date_str   = posting_date.strftime('%Y-%m-%d')
    has_errors = not df_duplicates.empty

    msg            = MIMEMultipart()
    msg['From']    = sender
    msg['To']      = ", ".join(recipients)
    msg['Subject'] = (
        f"⚠️ Transactions doublons détectées – {date_str}"
        if has_errors else
        f"✅ Aucun doublon – {date_str}"
    )

    if has_errors:
        rows_html = "".join(
            f"<tr><td>{row.requestID}</td>"
            f"<td style='text-align:center'>{row.nb}</td>"
            f"<td style='text-align:right'>{row.amount:,.2f}</td></tr>"
            for row in df_duplicates.itertuples()
        )
        body = f"""
        <html><body style="font-family:Arial,sans-serif;font-size:14px;">
          <h2 style="color:#d9534f;">⚠️ Doublons détectés – {date_str}</h2>
          <p><b>{len(df_duplicates)}</b> requestID(s) présentent des transactions doublons.</p>
          <table border="1" cellpadding="6" cellspacing="0"
                 style="border-collapse:collapse;width:60%;">
            <thead style="background:#f0f0f0;">
              <tr>
                <th>requestID</th>
                <th>Nb transactions</th>
                <th>Montant total</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
          <p style="color:#888;font-size:12px;">
            Voir le fichier Excel joint pour le détail complet.
          </p>
        </body></html>
        """
    else:
        body = f"""
        <html><body style="font-family:Arial,sans-serif;font-size:14px;">
          <h2 style="color:#28a745;">✅ Aucun doublon – {date_str}</h2>
          <p>Toutes les transactions du <b>{date_str}</b> sont uniques.</p>
        </body></html>
        """

    msg.attach(MIMEText(body, 'html', 'utf-8'))

    # Pièce jointe Excel si doublons
    if has_errors:
        buffer = BytesIO()
        df_duplicates.to_excel(buffer, index=False, sheet_name='Doublons')
        buffer.seek(0)
        attachment = MIMEApplication(buffer.read(), _subtype="xlsx")
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=f"doublons_{date_str}.xlsx",
        )
        msg.attach(attachment)

    try:
        with smtplib.SMTP('mail.pamf.mg', 25) as smtp:
            smtp.ehlo()
            smtp.sendmail(sender, recipients, msg.as_string())
        print(f"[OK] Email envoyé – {date_str}")
    except Exception as exc:
        print(f"[ERREUR] Envoi mail : {exc}")
        raise


# ─────────────────────────────────────────────
# 4. MAIN
# ─────────────────────────────────────────────

def main():
    yesterday = date.today() - timedelta(days=1)
    print(f"[INFO] Vérification des doublons pour : {yesterday}")

    try:
        con = get_connection()
        df  = pd.read_sql(QUERY, con, params=[yesterday])
        con.close()
    except Exception as exc:
        print(f"[ERREUR] Connexion / requête SQL : {exc}")
        raise

    print(f"[INFO] {len(df)} doublon(s) trouvé(s).")
    send_report(yesterday, df)


if __name__ == '__main__':
    main()