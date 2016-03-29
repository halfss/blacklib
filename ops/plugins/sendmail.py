#!/usr/bin/env python
# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText

from ops.options import get_options


smtp_options = [
    {
        "name": "smtp_uri",
        "default": "smtp://username:password@smtp_server:smtp_port",
        "help": "smtp auth info",
        "type": str,
    }]

options = get_options(smtp_options)

def send_mail(to_list,sub,content,html=False):
    smtp = options.smtp_uri
    mail_postfix = "gamewave.net"
    mail_host = smtp.split("@")[-1].split(":")[0]
    mail_user = smtp.split(":")[1].split("/")[-1]
    mail_pass = smtp.split("@")[0].split(":")[-1]
    me="AlertCenter"+"<"+mail_user+"@"+mail_postfix+">"
    if html:
        msg = MIMEText(content,_subtype='html',_charset='utf-8')
    else:
        msg = MIMEText(content,_charset='utf-8')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP()
        s.connect(mail_host)
        s.login(mail_user,mail_pass)
        s.sendmail(me, to_list, msg.as_string())
        s.close()
        return True
    except Exception, e:
        print e
        return False
