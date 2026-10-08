# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 16:45:34 2026

@author: m.razakasoa
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import pandas as pd
from io import BytesIO


def send_reconciliation_report(date, success=True, df_errors=None):
    sender = "no-reply@pamf.mg"
    recipients = ['m.razakasoa@pamf.mg','n.ramiaramananjafy@pamf.mg' ,'d.ravalison@pamf.mg']

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    # 🎯 Sujet dynamique
    if success:
        msg['Subject'] = f"Reconciliation SUCCESS - {date}"
    else:
        msg['Subject'] = f"Reconciliation FAILED - {date}"

    # 🎯 Body HTML
    if success:
        body = f"""
        <html>
        <body style="font-family: Arial;">
            <h2 style="color: #28a745;">Reconciliation réussie</h2>
            <p>Toutes les transactions du <b>{date}</b> ont été réconciliées avec succès.</p>
        </body>
        </html>
        """
    else:
        nb_errors = len(df_errors) if df_errors is not None else 0

        body = f"""
        <html>
        <body style="font-family: Arial;">
            <h2 style="color: #d9534f;">Echec de reconciliation</h2>
            <p>
                La reconciliation du <b>{date}</b> a échoué.
            </p>
            <p>
                <b>{nb_errors} transactions</b> ne sont pas réconciliées.
            </p>
            <p>Veuillez consulter la pièce jointe pour plus de détails.</p>
        </body>
        </html>
        """

    msg.attach(MIMEText(body, 'html', 'utf-8'))

    # 📎 Ajouter PJ si erreur
    if not success and df_errors is not None and not df_errors.empty:
        buffer = BytesIO()
        df_errors.to_excel(buffer, index=False)
        buffer.seek(0)

        attachment = MIMEApplication(buffer.read(), _subtype="xlsx")
        attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=f"reconciliation_errors_{date}.xlsx"
        )

        msg.attach(attachment)

    # 📡 Envoi
    try:
        with smtplib.SMTP('mail.pamf.mg', 25) as s:
            s.ehlo()
            s.sendmail(sender, recipients, msg.as_string())
            print("Email envoyé avec succès")

    except Exception as e:
        print(f"Erreur envoi mail: {e}")
        
if __name__ == "__main__":
    send_reconciliation_report('2026-01-01')