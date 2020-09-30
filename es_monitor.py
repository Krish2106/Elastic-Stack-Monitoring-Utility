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

fileName = '/run/ops_monitor/last_alert_times'

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
        body = {'roomId': '<>', 'markdown': markdownMessage}
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

        # The ES load balancer has a wide open access for port 9200, so any node can access this port
        # As other ELK components atleast has two nodes, a failure on Cluster health will send duplicate alerts, hence Kibana Node is used
        if self.service == 'kibana':
            esURL = 'http://%s:9200/_cluster/health' % sys.argv[1]
            esResp = requests.get(esURL).json()
            if esResp['status'] == 'red':
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

def node():
    # define a map with node name(using only component part as key) and the value as service running on it
    nodeService = {'master': 'elasticsearch', 'ingest': 'logstash', 'data': 'elasticsearch', 'kibana': 'kibana'}

    osNode = os.uname()[1]
    for node in nodeService:
        if node in osNode:
           return nodeService[node], osNode

def file_write():
    with open(fileName, 'a') as logfile:
        logfile.write(str(int(round(time.time()))) + '\n')

def main(args):
    # realert interval in seconds - 15 mins
    realertTime = 900

    currentTime = int(round(time.time()))

    service, hostname = node()
    monitor = SystemdStatus(service, hostname, args)
    if not monitor.is_active():
        # read file to capture the last alerted timestamp
        if os.stat(fileName).st_size != 0:
            with open(fileName, 'rb') as f:
                last_alert_time = int(f.readlines()[-1])
        else:
            last_alert_time = int()

        if currentTime - last_alert_time > realertTime:
            file_write()
            # send alerts
            monitor.webex_alert()
            monitor.send_pd_alert()
            logging.info('ops_monitor[%s]: INFO: %s service is Down - Post Alert sent' %(os.getpid(),service))
        else:
            logging.info('ops_monitor[%s]: INFO: %s service is Down - Post Alert Skipped' %(os.getpid(),service))
    else:
        logging.info('ops_monitor[%s]: INFO: %s service is UP' %(os.getpid(),service))


if __name__ == '__main__':

    # args - ElasticSearch Rest Client VIP
    sys.exit(main(sys.argv[1]))