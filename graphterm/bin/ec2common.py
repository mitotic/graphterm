"""
ec2common: Common code to manage Amazon AWS EC2 instances
"""

import boto
import os
import re
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

def get_hosted_zone(route53conn, domain_name):
    retval = route53conn.get_hosted_zone_by_name(domain_name)
    if retval:
        return retval['GetHostedZoneResponse']["HostedZone"]
    else:
        return None

def create_hosted_zone(route53conn, domain_name):
    # Create new hosted zone
    retval = route53conn.create_hosted_zone(domain_name+".")
    try:
        return retval['CreateHostedZoneResponse']["HostedZone"]
    except Exception:
        raise Exception("Failed to create hosted zone %s; is Route 53 service activated?" % domain_name)

def get_zone_id(hosted_zone):
    return hosted_zone['Id'].replace('/hostedzone/', '')

def get_nameservers(route53conn, domain_name):
    hosted_zone = get_hosted_zone(route53conn, domain_name)
    if hosted_zone:
        for rec in route53conn.get_all_rrsets(get_zone_id(hosted_zone)):
            if rec.type == "NS":
                return rec.to_print()
    return None

def cname(route53conn, zone, domain_name, alt_name, ttl=60, remove=False):
    from boto.route53.record import ResourceRecordSets
    
    zone_id = get_zone_id(zone)
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

def get_instance_props(name=None):
    """Return property lists for all instances with id or tag matching name (with simple shell wildcarding)"""
    if name and ("?" in name or "*" in name or "[" in name):
        name_re = re.compile("^"+name.replace("+", "\\+").replace(".", "\\.").replace("?", ".?").replace("*", ".*")+"$")
    else:
        name_re = None
        
    ec2 = get_ec2()

    all_instances = ec2.get_all_instances()
    props_list = []
    for res in all_instances:
        iobj = res.instances[0]
        if name_re:
            matched = any(name_re.match(tag) for tag in iobj.tags)
        elif name:
            matched = name == iobj.id or any(name == tag for tag in iobj.tags)
        else:
            matched = True
        if matched:
            props = {"id": iobj.id,
                     "public_dns": iobj.public_dns_name,
                     "key": iobj.key_name,
                     "state": iobj.state,
                     "tags": iobj.tags}
            props_list.append(props)

    return props_list
