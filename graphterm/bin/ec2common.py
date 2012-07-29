"""
ec2common: Common code to manage Amazon AWS EC2 instances
"""

import boto
import os
import sys
import time

from boto.route53.connection import Route53Connection

boto_config = """Create the file ~/.boto containing:
   [Credentials]
   aws_access_key_id = ACCESS_KEY
   aws_secret_access_key = SECRET_KEY
"""

if not os.path.exists(os.path.expanduser("~/.boto")):
    print >> sys.stderr, boto_config
    sys.exit(1)

def get_zone(zone_domain):
    route53conn = Route53Connection()

    results = route53conn.get_all_hosted_zones()
    zones = results['ListHostedZonesResponse']['HostedZones']

    for zone in zones:
        if zone['Name'] == zone_domain+".":
            return route53conn, zone

    return (route53conn, None)

def cname(route53conn, zone, domain_name, alt_name, ttl=60, remove=False):
    from boto.route53.record import ResourceRecordSets
    zone_id = zone['Id'].replace('/hostedzone/', '')
    changes = ResourceRecordSets(route53conn, zone_id)
    change = changes.add_change("DELETE" if remove else "CREATE",
                                name=domain_name,
                                type="CNAME", ttl=ttl)
    if alt_name:
        change.add_value(alt_name)
    changes.commit()

def get_ec2():
    return boto.connect_ec2()

def kill(instance_ids=[]):
    ec2 = get_ec2()
    ec2.terminate_instances(instance_ids=instance_ids)

def get_instance_props(instance_id=None):
    ec2 = get_ec2()

    all_instances = ec2.get_all_instances()
    props_list = []
    for res in all_instances:
        iobj = res.instances[0]
        if not instance_id or instance_id == iobj.id or any(tag.startswith(instance_id) for tag in iobj.tags):
            props = {"id": iobj.id,
                     "public_dns": iobj.public_dns_name,
                     "key": iobj.key_name,
                     "state": iobj.state,
                     "tags": iobj.tags}
            props_list.append(props)

    return props_list
