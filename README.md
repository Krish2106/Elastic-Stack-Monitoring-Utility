# Elastic-Stack-Monitoring-Utility

A basic python utlility to monitor the Elasticsearch services and send out an alert to Spark Webhooks / PagerDuty emails. 

The Script can be deployed across the hosts running the ELK instances. (This assumes each component has its own host). 

Using Ansible this can be done as below

- hosts: all
  become: yes
  tasks:
    - name: Copy ELK monitoring python script
      copy: src=es_monitor.py dest=/usr/local/sbin/es_monitor.py owner=root group=root mode=755

    - name: Run Python monitoring script
      command: python /usr/local/sbin/es_monitor.py {{ elasticsearch restclient IP}}


The keys in dictionary  nodeService = {'master': 'elasticsearch', 'ingest': 'logstash', 'data': 'elasticsearch', 'kibana': 'kibana'} should be changed to match the component name representing the host 

Eg: To monitor elasticsearch service running on host elk-master-01 , set nodeService = {'master': 'elasticsearch'}
