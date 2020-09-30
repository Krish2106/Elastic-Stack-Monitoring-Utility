# Elastic-Stack-Monitoring-Utility

A basic python utlility to monitor the Elasticsearch services and send out an alert to Spark Webhooks / PagerDuty emails. A realerting mechanism is added so as on outage doesn't cause a flood of alerts rather handles in a controlled way.

The Script can be deployed as a Cron job across the hosts running the ELK instances through a playbook. (This assumes each component has its own host).

The keys in dictionary  nodeService = {'master': 'elasticsearch', 'ingest': 'logstash', 'data': 'elasticsearch', 'kibana': 'kibana'} should be changed to match the component name representing the host

Eg: To monitor elasticsearch service running on host elk-master-01 , set nodeService = {'master': 'elasticsearch'}
