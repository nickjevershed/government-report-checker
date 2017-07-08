#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import os
from datetime import datetime
dt = datetime.now()
print dt.isoformat(" ")

EMAIL_ALERT_PASSWORD = os.environ['EMAIL_ALERT_PASSWORD']

fromaddr = "alerts@nickevershed.com"
toaddr = "nick.evershed@theguardian.com"
 
msg = MIMEMultipart()
 
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Report checker"
body = "YOUR MESSAGE HERE"
msg.attach(MIMEText(body, 'plain'))
 
server = smtplib.SMTP_SSL('mail.nickevershed.com', 465)
server.login(fromaddr, EMAIL_ALERT_PASSWORD)
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()

print "done"