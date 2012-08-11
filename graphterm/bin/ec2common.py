"""
ec2common: Common code to manage Amazon AWS EC2 instances
"""

import boto
import os
import sys
import time

from boto.route53.connection import Route53Connection

import gtermapi

AUTH_FORMAT = """[Credentials]
access_key_id = %(access_key_id)s
secret_access_key = %(secret_access_key)s
"""

Auth_parser = gtermapi.FormParser(title='Enter AWS Access Credentials<br>(Usually at <a href="https://portal.aws.amazon.com/gp/aws/securityCredentials" target="_blank">https://portal.aws.amazon.com/gp/aws/securityCredentials</a>)<p>')

Auth_parser.add_option("access_key_id", label="AWS Access Key ID: ", help="AWS Access Key ID")
Auth_parser.add_option("secret_access_key", label="AWS Secret Access Key: ", help="AWS Secret Access Key")

def check_auth_file(auth_file):
    auth_file = os.path.expanduser(auth_file)
    if not os.path.isfile(auth_file):
        if not sys.stdout.isatty():
            print >> sys.stderr, "Authentication file %s not found!" % (auth_file,)
            sys.exit(1)
        try:
            form_values = Auth_parser.read_input(trim=True)
            if not form_values:
                raise Exception("Form input cancelled")

            if not all(form_values.values()):
                raise Exception("Missing authentication data")
                
            with os.fdopen( os.open(auth_file, os.O_WRONLY|os.O_CREAT, 0600), "w") as f:
                f.write(AUTH_FORMAT % form_values)
            print >> sys.stderr, "Created authentication file %s; re-type command" % auth_file
            sys.exit(1)
        except Exception, excp:
            print >> sys.stderr, "Error in creating authentication file: %s" % excp
            sys.exit(1)

Default_auth_file = "~/.boto"

check_auth_file(Default_auth_file)


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
