#!/usr/bin/env python2.7

from email.mime.text import MIMEText
import json
import logging
from logging.handlers import SysLogHandler
import os
import requests
import smtplib
import subprocess
import sys
import time


class SystemdStatus(object):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(SysLogHandler('/dev/log'))

    def __init__(self, service, host, esHost):
        self.service = service
        self.host = host
        self.esHost = esHost

    def webex_alert(self):
        url = 'v1/webex/spark/endpoint'
        markdownMessage = '**%s - %s Down**' %(self.service, self.host)
        body = {'roomId': 'roomID123', 'markdown': markdownMessage}
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer <Token>'}

        try:
            requests.post(url, data = json.dumps(body), headers = headers)
        except requests.exceptions.RequestException as e:
            logging.error(e)

    def send_pd_alert(self):
        body = '%s Service is Down on %s\n' % (self.service, self.host)
        msg = MIMEText(body)
        msg['Subject'] = '[Operations Alert] %s Down' % (self.service)
        msg['From'] = 'foo@xyz.com'
        msg['To'] = 'bar@pagerduty.com'

        try:
            server = smtplib.SMTP('mailserver.com', port = 25)
            server.sendmail('foo@xyz.com', 'bar@pagerduty.com', msg.as_string())
            server.quit()
        except smtplib.SMTPResponseException as e:
            logging.error(e)


    def is_active(self):

        # Optionally ElasticSearch Cluster health can be monitored using the rest client on its default port 9200 
        # One of the ELK nodes can be chosen to perform the Health check, here the node hosting Kibana does the check
        if self.service == 'kibana':
            esURL = 'http://%s:9200/_cluster/health' % sys.argv[1]
            esResp = requests.get(esURL).json()
            if esResp['status'] == 'red' or esResp['status'] == 'yellow':
                return False

        # check status of systemd services
        systemctlCmd = 'systemctl status %s' % self.service
        proc = subprocess.Popen(systemctlCmd, shell = True,stdout = subprocess.PIPE)
        stdoutList = proc.communicate()[0].split('\n')
        for val in stdoutList:
            if 'Active:' in val:
                if '(running)' in val:
                    return True
        return False


if __name__ == '__main__':

    # define a map with node name(using service-component part as key) and the value as service running on it
    nodeService = {'master': 'elasticsearch', 'ingest': 'logstash', 'data': 'elasticsearch', 'kibana': 'kibana'}

    # realert interval in seconds 10 mins
    realertTime = 600

    # Monitoring utility sleep interval
    sleepInterval = 60

    # lastAlerted Time in seconds
    lastAlertTime = int()

    # capture host name using uname command
    osNode = os.uname()[1]
    for node in nodeService:
        if node in osNode:
            monitor = SystemdStatus(nodeService[node], osNode, sys.argv[1])
            while True:
                currentTime = int(round(time.time()))
                logging.debug("lastAlertTime is %s and currentTime is %s" %(lastAlertTime, currentTime))
                if not monitor.is_active():
                    logging.info('%s service is DOWN' % nodeService[node])
                    if currentTime - lastAlertTime > realertTime:
                        lastAlertTime = currentTime
                        monitor.webex_alert()
                        monitor.send_pd_alert()
                    else:
                        logging.info('%s service is Down - Post Alert Skipped' % nodeService[node])
                logging.info('%s service is UP , sleeping for %s seconds' %(nodeService[node], sleepInterval))
                time.sleep(sleepInterval)
