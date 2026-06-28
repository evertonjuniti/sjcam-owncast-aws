import boto3
import os
import json
import logging
import time
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

region = os.environ['REGION']
ec2 = boto3.client('ec2', region_name=region)
ssm = boto3.client('ssm', region_name=region)

PUBLIC_NACL_ID         = os.environ['PUBLIC_NACL_ID']
PROXY_INSTANCE_ID      = os.environ['PROXY_INSTANCE_ID']
MAINTENANCE_SG_ID      = os.environ['MAINTENANCE_SG_ID']
INSTANCE_PROFILE_NAME  = os.environ['INSTANCE_PROFILE_NAME']
PROXY_DOMAIN           = os.environ['PROXY_DOMAIN']
PRIVATE_NACL_ID        = os.environ['PRIVATE_NACL_ID']
OWNCAST_INSTANCE_ID    = os.environ['OWNCAST_INSTANCE_ID']
PRIVATE_ROUTE_TABLE_ID  = os.environ['PRIVATE_ROUTE_TABLE_ID']
INTERNET_GATEWAY_ID     = os.environ['INTERNET_GATEWAY_ID']
ELASTIC_IP_ALLOC_ID     = os.environ['ELASTIC_IP_ALLOC_ID']

# NACL rules for Public Subnet (Proxy) - temporary maintenance access.
# Inbound: SSH (22) for direct access; ephemeral TCP ports (1024-65535) for
# return traffic from outbound connections made by the instance.
INBOUND_RULES = [
    {'from_port': 22,   'to_port': 22,    'protocol': '6',  'description': 'SSH'},
    {'from_port': 1024, 'to_port': 65535, 'protocol': '6',  'description': 'Custom TCP ephemeral ports'},
]

# Outbound: HTTP (80) and HTTPS (443) for apt package downloads;
# DNS/UDP (53) for hostname resolution during apt update/upgrade.
OUTBOUND_RULES = [
    {'from_port': 80,  'to_port': 80,  'protocol': '6',  'description': 'HTTP'},
    {'from_port': 53,  'to_port': 53,  'protocol': '17', 'description': 'DNS UDP'},
    {'from_port': 443, 'to_port': 443, 'protocol': '6',  'description': 'HTTPS'},
]

# NACL rules for Private Subnet (Owncast) - temporary maintenance access.
# Inbound: RTMP (1935) and web (8080) for streaming; SSH (22) for direct access.
# Outbound: HTTP (80), DNS/UDP (53), ephemeral TCP (1024-65535) for internet access.
OWNCAST_INBOUND_RULES = [
    {'from_port': 1935, 'to_port': 1935,  'protocol': '6',  'description': 'RTMP'},
    {'from_port': 8080, 'to_port': 8080,  'protocol': '6',  'description': 'HTTP Owncast'},
    {'from_port': 22,   'to_port': 22,    'protocol': '6',  'description': 'SSH'},
    {'from_port': 1024, 'to_port': 65535, 'protocol': '6',  'description': 'Custom TCP ephemeral ports'},
]

OWNCAST_OUTBOUND_RULES = [
    {'from_port': 80,   'to_port': 80,    'protocol': '6',  'description': 'HTTP'},
    {'from_port': 53,   'to_port': 53,    'protocol': '17', 'description': 'DNS UDP'},
    {'from_port': 443,  'to_port': 443,   'protocol': '6',  'description': 'HTTPS'},
    {'from_port': 1024, 'to_port': 65535, 'protocol': '6',  'description': 'Custom TCP ephemeral ports'},
]


def lambda_handler(event, context):
    results = {}

    mode = event.get('mode', '').strip().lower()
    valid_modes = ('proxy-os-update', 'proxy-cert-renew', 'owncast-os-update')
    if mode not in valid_modes:
        msg = f"Invalid or missing 'mode' in event payload. Valid values: {valid_modes}. Got: '{mode}'"
        logger.error(msg)
        return {'statusCode': 400, 'body': json.dumps({'error': msg})}

    logger.info("=" * 65)
    logger.info("OWNCAST MAINTENANCE LAMBDA - STARTED")
    logger.info(f"  Mode     : {mode.upper()}")
    if mode in ('proxy-os-update', 'proxy-cert-renew'):
        logger.info(f"  Instance : {PROXY_INSTANCE_ID}")
        logger.info(f"  Domain   : {PROXY_DOMAIN}")
    else:
        logger.info(f"  Instance : {OWNCAST_INSTANCE_ID}")
    logger.info("=" * 65)

    if mode in ('proxy-os-update', 'proxy-cert-renew'):
        # ------------------------------------------------------------ Setup
        logger.info("PHASE 1/3 - SETUP")
        logger.info("-" * 65)

        logger.info("[SETUP 1/3] Opening temporary NACL inbound/outbound rules")
        try:
            results['nacl_open'] = _open_nacl_rules()
            r = results['nacl_open']
            logger.info(f"[SETUP 1/3] OK - added={r.get('added', [])}, skipped={r.get('skipped', [])}")
        except ClientError as e:
            logger.error(f"[SETUP 1/3] FAILED - {str(e)}", exc_info=True)
            results['nacl_open'] = {'error': str(e)}

        logger.info("[SETUP 2/3] Adding Maintenance Security Group to Proxy instance")
        try:
            results['security_group_add'] = _add_maintenance_sg(PROXY_INSTANCE_ID)
            logger.info(f"[SETUP 2/3] OK - action={results['security_group_add'].get('action')}")
        except ClientError as e:
            logger.error(f"[SETUP 2/3] FAILED - {str(e)}", exc_info=True)
            results['security_group_add'] = {'error': str(e)}

        logger.info("[SETUP 3/3] Assigning IAM instance profile to Proxy instance")
        try:
            results['iam_instance_profile_add'] = _assign_iam_instance_profile(PROXY_INSTANCE_ID)
            logger.info(f"[SETUP 3/3] OK - action={results['iam_instance_profile_add'].get('action')}")
        except ClientError as e:
            logger.error(f"[SETUP 3/3] FAILED - {str(e)}", exc_info=True)
            results['iam_instance_profile_add'] = {'error': str(e)}

        # ---------------------------------------------------------- Main work
        logger.info("=" * 65)
        logger.info(f"PHASE 2/3 - MAIN WORK ({mode.upper()})")
        logger.info("-" * 65)

        if mode == 'proxy-os-update':
            logger.info("[MAIN WORK] Running: apt update + apt upgrade")
            try:
                results['apt_maintenance'] = _run_os_update(PROXY_INSTANCE_ID)
                logger.info("[MAIN WORK] OK - OS update/upgrade completed successfully")
            except (ClientError, RuntimeError) as e:
                logger.error(f"[MAIN WORK] FAILED - {str(e)}", exc_info=True)
                results['apt_maintenance'] = {'error': str(e)}
        else:  # proxy-cert-renew
            logger.info("[MAIN WORK] Running: certbot renew + cert bundle + haproxy restart")
            try:
                results['apt_maintenance'] = _run_cert_renew()
                logger.info("[MAIN WORK] OK - Certificate renewal completed successfully")
            except (ClientError, RuntimeError) as e:
                logger.error(f"[MAIN WORK] FAILED - {str(e)}", exc_info=True)
                results['apt_maintenance'] = {'error': str(e)}

        # ------------------------------------------------------------ Teardown
        logger.info("=" * 65)
        logger.info("PHASE 3/3 - TEARDOWN (always runs regardless of earlier errors)")
        logger.info("-" * 65)

        logger.info("[TEARDOWN 1/4] Stopping Proxy instance")
        try:
            results['instance_stop'] = _stop_instance(PROXY_INSTANCE_ID)
            logger.info(f"[TEARDOWN 1/4] OK - action={results['instance_stop'].get('action')}")
        except (ClientError, RuntimeError) as e:
            logger.error(f"[TEARDOWN 1/4] FAILED - {str(e)}", exc_info=True)
            results['instance_stop'] = {'error': str(e)}

        logger.info("[TEARDOWN 2/4] Disassociating IAM instance profile from Proxy instance")
        try:
            results['iam_instance_profile_remove'] = _disassociate_iam_instance_profile(PROXY_INSTANCE_ID)
            logger.info(f"[TEARDOWN 2/4] OK - action={results['iam_instance_profile_remove'].get('action')}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 2/4] FAILED - {str(e)}", exc_info=True)
            results['iam_instance_profile_remove'] = {'error': str(e)}

        logger.info("[TEARDOWN 3/4] Removing Maintenance Security Group from Proxy instance")
        try:
            results['security_group_remove'] = _remove_maintenance_sg(PROXY_INSTANCE_ID)
            logger.info(f"[TEARDOWN 3/4] OK - action={results['security_group_remove'].get('action')}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 3/4] FAILED - {str(e)}", exc_info=True)
            results['security_group_remove'] = {'error': str(e)}

        logger.info("[TEARDOWN 4/4] Closing temporary NACL rules")
        try:
            results['nacl_close'] = _close_nacl_rules()
            r = results['nacl_close']
            logger.info(f"[TEARDOWN 4/4] OK - deleted={r.get('deleted', [])}, not_found={r.get('not_found', [])}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 4/4] FAILED - {str(e)}", exc_info=True)
            results['nacl_close'] = {'error': str(e)}

    else:  # owncast-os-update
        # ------------------------------------------------------------ Setup
        logger.info("PHASE 1/3 - SETUP")
        logger.info("-" * 65)

        logger.info("[SETUP 1/4] Adding Internet Gateway route to Private Subnet Route Table")
        try:
            results['route_igw_add'] = _add_route_to_igw()
            logger.info(f"[SETUP 1/4] OK - action={results['route_igw_add'].get('action')}")
        except ClientError as e:
            logger.error(f"[SETUP 1/4] FAILED - {str(e)}", exc_info=True)
            results['route_igw_add'] = {'error': str(e)}

        logger.info("[SETUP 2/4] Opening temporary NACL inbound/outbound rules for Private Subnet")
        try:
            results['nacl_open'] = _open_owncast_nacl_rules()
            r = results['nacl_open']
            logger.info(f"[SETUP 2/4] OK - added={r.get('added', [])}, skipped={r.get('skipped', [])}")
        except ClientError as e:
            logger.error(f"[SETUP 2/4] FAILED - {str(e)}", exc_info=True)
            results['nacl_open'] = {'error': str(e)}

        logger.info("[SETUP 3/4] Adding Maintenance Security Group to Owncast instance")
        try:
            results['security_group_add'] = _add_maintenance_sg(OWNCAST_INSTANCE_ID)
            logger.info(f"[SETUP 3/4] OK - action={results['security_group_add'].get('action')}")
        except ClientError as e:
            logger.error(f"[SETUP 3/4] FAILED - {str(e)}", exc_info=True)
            results['security_group_add'] = {'error': str(e)}

        logger.info("[SETUP 4/5] Assigning IAM instance profile to Owncast instance")
        try:
            results['iam_instance_profile_add'] = _assign_iam_instance_profile(OWNCAST_INSTANCE_ID)
            logger.info(f"[SETUP 4/5] OK - action={results['iam_instance_profile_add'].get('action')}")
        except ClientError as e:
            logger.error(f"[SETUP 4/5] FAILED - {str(e)}", exc_info=True)
            results['iam_instance_profile_add'] = {'error': str(e)}

        logger.info("[SETUP 5/5] Associating Elastic IP with Owncast instance for internet access")
        try:
            results['elastic_ip_add'] = _associate_elastic_ip()
            logger.info(f"[SETUP 5/5] OK - action={results['elastic_ip_add'].get('action')}")
        except ClientError as e:
            logger.error(f"[SETUP 5/5] FAILED - {str(e)}", exc_info=True)
            results['elastic_ip_add'] = {'error': str(e)}

        # ---------------------------------------------------------- Main work
        logger.info("=" * 65)
        logger.info("PHASE 2/3 - MAIN WORK (OWNCAST-OS-UPDATE)")
        logger.info("-" * 65)

        logger.info("[MAIN WORK] Running: apt update + apt upgrade on Owncast instance")
        try:
            results['apt_maintenance'] = _run_os_update(OWNCAST_INSTANCE_ID)
            logger.info("[MAIN WORK] OK - Owncast OS update/upgrade completed successfully")
        except (ClientError, RuntimeError) as e:
            logger.error(f"[MAIN WORK] FAILED - {str(e)}", exc_info=True)
            results['apt_maintenance'] = {'error': str(e)}

        # ------------------------------------------------------------ Teardown
        logger.info("=" * 65)
        logger.info("PHASE 3/3 - TEARDOWN (always runs regardless of earlier errors)")
        logger.info("-" * 65)

        logger.info("[TEARDOWN 1/6] Stopping Owncast instance")
        try:
            results['instance_stop'] = _stop_instance(OWNCAST_INSTANCE_ID)
            logger.info(f"[TEARDOWN 1/6] OK - action={results['instance_stop'].get('action')}")
        except (ClientError, RuntimeError) as e:
            logger.error(f"[TEARDOWN 1/6] FAILED - {str(e)}", exc_info=True)
            results['instance_stop'] = {'error': str(e)}

        logger.info("[TEARDOWN 2/6] Disassociating Elastic IP from Owncast instance")
        try:
            results['elastic_ip_remove'] = _disassociate_elastic_ip()
            logger.info(f"[TEARDOWN 2/6] OK - action={results['elastic_ip_remove'].get('action')}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 2/6] FAILED - {str(e)}", exc_info=True)
            results['elastic_ip_remove'] = {'error': str(e)}

        logger.info("[TEARDOWN 3/6] Disassociating IAM instance profile from Owncast instance")
        try:
            results['iam_instance_profile_remove'] = _disassociate_iam_instance_profile(OWNCAST_INSTANCE_ID)
            logger.info(f"[TEARDOWN 3/6] OK - action={results['iam_instance_profile_remove'].get('action')}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 3/6] FAILED - {str(e)}", exc_info=True)
            results['iam_instance_profile_remove'] = {'error': str(e)}

        logger.info("[TEARDOWN 4/6] Removing Maintenance Security Group from Owncast instance")
        try:
            results['security_group_remove'] = _remove_maintenance_sg(OWNCAST_INSTANCE_ID)
            logger.info(f"[TEARDOWN 4/6] OK - action={results['security_group_remove'].get('action')}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 4/6] FAILED - {str(e)}", exc_info=True)
            results['security_group_remove'] = {'error': str(e)}

        logger.info("[TEARDOWN 5/6] Closing temporary NACL rules for Private Subnet")
        try:
            results['nacl_close'] = _close_owncast_nacl_rules()
            r = results['nacl_close']
            logger.info(f"[TEARDOWN 5/6] OK - deleted={r.get('deleted', [])}, not_found={r.get('not_found', [])}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 5/6] FAILED - {str(e)}", exc_info=True)
            results['nacl_close'] = {'error': str(e)}

        logger.info("[TEARDOWN 6/6] Removing Internet Gateway route from Private Subnet Route Table")
        try:
            results['route_igw_remove'] = _remove_route_to_igw()
            logger.info(f"[TEARDOWN 6/6] OK - action={results['route_igw_remove'].get('action')}")
        except ClientError as e:
            logger.error(f"[TEARDOWN 6/6] FAILED - {str(e)}", exc_info=True)
            results['route_igw_remove'] = {'error': str(e)}

    has_errors = any('error' in v for v in results.values())
    status_code = 500 if has_errors else 200
    outcome = "COMPLETED WITH ERRORS" if has_errors else "COMPLETED SUCCESSFULLY"

    logger.info("=" * 65)
    logger.info(f"OWNCAST MAINTENANCE LAMBDA - {outcome} | MODE={mode.upper()} | HTTP {status_code}")
    logger.info("=" * 65)
    return {
        'statusCode': status_code,
        'body': json.dumps(results)
    }


# ---------------------------------------------------------------------------
# NACL helpers
# ---------------------------------------------------------------------------

def _nacl_allow_rule_exists(entries, egress, from_port, to_port, protocol, cidr='0.0.0.0/0'):
    """Return True if an ALLOW entry already covers the given port/protocol/cidr."""
    for entry in entries:
        if entry.get('Egress') != egress:
            continue
        if entry.get('CidrBlock') != cidr:
            continue
        if entry.get('Protocol') != protocol:
            continue
        if entry.get('RuleAction') != 'allow':
            continue
        port_range = entry.get('PortRange', {})
        if port_range.get('From') == from_port and port_range.get('To') == to_port:
            return True
    return False


def _next_rule_number(entries, egress):
    """Return the next available rule number (last existing number + 1), minimum 100.
    Rule numbers 32767 (IPv4 default deny) and 32768 (IPv6 default deny) are
    reserved by AWS and must be excluded from the candidate set."""
    numbers = [
        e['RuleNumber'] for e in entries
        if e.get('Egress') == egress and e['RuleNumber'] < 32767
    ]
    return (max(numbers) + 1) if numbers else 100


def _open_nacl_rules():
    logger.info(f"  Fetching current NACL entries for {PUBLIC_NACL_ID}")
    response = ec2.describe_network_acls(NetworkAclIds=[PUBLIC_NACL_ID])
    entries = response['NetworkAcls'][0]['Entries']

    added   = []
    skipped = []

    next_inbound = _next_rule_number(entries, egress=False)
    for rule in INBOUND_RULES:
        if _nacl_allow_rule_exists(entries, False, rule['from_port'], rule['to_port'], rule['protocol']):
            logger.info(f"  [SKIP] Inbound rule already exists: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            skipped.append(f"inbound-{rule['description']}")
            continue

        ec2.create_network_acl_entry(
            NetworkAclId=PUBLIC_NACL_ID,
            RuleNumber=next_inbound,
            Protocol=rule['protocol'],
            RuleAction='allow',
            Egress=False,
            CidrBlock='0.0.0.0/0',
            PortRange={'From': rule['from_port'], 'To': rule['to_port']}
        )
        logger.info(f"  [ADD ] Inbound NACL rule #{next_inbound}: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
        added.append(f"inbound-{rule['description']}")
        next_inbound += 1

    next_outbound = _next_rule_number(entries, egress=True)
    for rule in OUTBOUND_RULES:
        if _nacl_allow_rule_exists(entries, True, rule['from_port'], rule['to_port'], rule['protocol']):
            logger.info(f"  [SKIP] Outbound rule already exists: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            skipped.append(f"outbound-{rule['description']}")
            continue

        ec2.create_network_acl_entry(
            NetworkAclId=PUBLIC_NACL_ID,
            RuleNumber=next_outbound,
            Protocol=rule['protocol'],
            RuleAction='allow',
            Egress=True,
            CidrBlock='0.0.0.0/0',
            PortRange={'From': rule['from_port'], 'To': rule['to_port']}
        )
        logger.info(f"  [ADD ] Outbound NACL rule #{next_outbound}: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
        added.append(f"outbound-{rule['description']}")
        next_outbound += 1

    logger.info(f"  NACL open summary: {len(added)} rule(s) added, {len(skipped)} skipped")
    return {'added': added, 'skipped': skipped}


# ---------------------------------------------------------------------------
# IAM instance profile helper
# ---------------------------------------------------------------------------

def _assign_iam_instance_profile(instance_id):
    """Associate INSTANCE_PROFILE_NAME with the given instance.
    If an instance profile is already associated, replace it; otherwise create
    a fresh association."""
    logger.info(f"  Checking current IAM instance profile on {instance_id}")
    iam_profile = {'Name': INSTANCE_PROFILE_NAME}

    assoc_response = ec2.describe_iam_instance_profile_associations(
        Filters=[{'Name': 'instance-id', 'Values': [instance_id]}]
    )
    associations = assoc_response.get('IamInstanceProfileAssociations', [])

    # Keep only active/associating associations (ignore disassociating ones)
    active = [
        a for a in associations
        if a.get('State') in ('associated', 'associating')
    ]

    if active:
        current_name = active[0].get('IamInstanceProfile', {}).get('Arn', '').split('/')[-1]
        if current_name == INSTANCE_PROFILE_NAME:
            logger.info(f"  [SKIP] Profile '{INSTANCE_PROFILE_NAME}' already associated with {instance_id}")
            return {'action': 'skipped', 'reason': 'already_associated'}

        association_id = active[0]['AssociationId']
        ec2.replace_iam_instance_profile_association(
            IamInstanceProfile=iam_profile,
            AssociationId=association_id
        )
        logger.info(f"  [REPLACE] Replaced existing profile with '{INSTANCE_PROFILE_NAME}' on {instance_id}")
        return {'action': 'replaced', 'instance_profile_name': INSTANCE_PROFILE_NAME}

    ec2.associate_iam_instance_profile(
        IamInstanceProfile=iam_profile,
        InstanceId=instance_id
    )
    logger.info(f"  [ADD ] Associated profile '{INSTANCE_PROFILE_NAME}' with {instance_id}")
    return {'action': 'associated', 'instance_profile_name': INSTANCE_PROFILE_NAME}


# ---------------------------------------------------------------------------
# Security Group helper
# ---------------------------------------------------------------------------

def _add_maintenance_sg(instance_id):
    """Add MAINTENANCE_SG_ID to the given instance without removing existing groups."""
    logger.info(f"  Checking security groups on {instance_id}")
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    current_sg_ids = [sg['GroupId'] for sg in instance['SecurityGroups']]
    logger.info(f"  Current SGs: {current_sg_ids}")

    if MAINTENANCE_SG_ID in current_sg_ids:
        logger.info(f"  [SKIP] Maintenance SG {MAINTENANCE_SG_ID} already attached")
        return {'action': 'skipped', 'reason': 'already_attached'}

    ec2.modify_instance_attribute(
        InstanceId=instance_id,
        Groups=current_sg_ids + [MAINTENANCE_SG_ID]
    )
    logger.info(f"  [ADD ] Maintenance SG {MAINTENANCE_SG_ID} added to {instance_id}")
    return {'action': 'added', 'security_group_id': MAINTENANCE_SG_ID}


# ---------------------------------------------------------------------------
# Shared SSM / instance helpers (accept instance_id parameter)
# NOTE: Lambda timeout must be configured to at least 900 seconds (15 minutes)
# ---------------------------------------------------------------------------

def _ensure_instance_running(instance_id):
    """Start the given instance if not already running and wait until it is."""
    logger.info(f"  Querying state of instance {instance_id}")
    response = ec2.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    logger.info(f"  Current state: [{state.upper()}]")

    if state == 'running':
        logger.info(f"  [OK  ] Instance already running, no action needed")
        return {'action': 'already_running'}

    if state in ('terminated', 'shutting-down'):
        raise RuntimeError(f"Instance {instance_id} is in unrecoverable state: {state}")

    if state == 'stopping':
        logger.info(f"  [WAIT] Instance is stopping; waiting for 'stopped' before starting...")
        for _ in range(12):  # up to ~2 minutes
            time.sleep(10)
            resp = ec2.describe_instances(InstanceIds=[instance_id])
            if resp['Reservations'][0]['Instances'][0]['State']['Name'] == 'stopped':
                break

    if state in ('stopped', 'stopping'):
        ec2.start_instances(InstanceIds=[instance_id])
        logger.info(f"  [START] Start signal sent to instance {instance_id}")
    # else 'pending': already starting, fall through to poll loop

    for attempt in range(24):  # up to ~4 minutes
        time.sleep(10)
        resp = ec2.describe_instances(InstanceIds=[instance_id])
        current_state = resp['Reservations'][0]['Instances'][0]['State']['Name']
        logger.info(f"  [POLL {attempt + 1:02d}/24] Instance state: [{current_state.upper()}]")
        if current_state == 'running':
            logger.info(f"  [OK  ] Instance is now running (after {attempt + 1} poll(s), ~{(attempt + 1) * 10}s)")
            return {'action': 'started', 'polls': attempt + 1}
        if current_state in ('terminated', 'shutting-down'):
            raise RuntimeError(f"Instance entered unexpected state: {current_state}")

    raise RuntimeError(f"Instance {instance_id} did not reach 'running' state within timeout")


def _wait_for_ssm_agent(instance_id, max_polls=24):
    """Wait until the SSM agent on the given instance reports as Online."""
    logger.info(f"  Polling SSM agent on {instance_id} (max {max_polls} polls x 10s = ~{max_polls * 10}s)")
    for attempt in range(max_polls):  # up to ~4 minutes
        time.sleep(10)
        response = ssm.describe_instance_information(
            Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
        )
        instances = response.get('InstanceInformationList', [])
        if instances and instances[0].get('PingStatus') == 'Online':
            logger.info(f"  [OK  ] SSM agent is ONLINE after {attempt + 1} poll(s) (~{(attempt + 1) * 10}s)")
            return {'polls': attempt + 1}
        ping = instances[0].get('PingStatus', 'not registered') if instances else 'not registered'
        logger.info(f"  [POLL {attempt + 1:02d}/{max_polls}] SSM agent status: {ping}")

    raise RuntimeError(f"SSM agent on {instance_id} did not come online within timeout")


def _run_ssm_command(instance_id, commands, label, timeout_seconds=600):
    """Send shell commands via SSM Run Command to the given instance and poll until complete."""
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': commands},
        TimeoutSeconds=timeout_seconds,
        Comment=label
    )
    command_id = response['Command']['CommandId']
    logger.info(f"  [DISPATCH] SSM command sent | label='{label}' | id={command_id} | timeout={timeout_seconds}s")

    poll_interval = 15
    # Poll for longer than the SSM timeout so the Lambda loop never exhausts
    # before SSM reports a terminal status (Success/Failed/TimedOut/etc.).
    # Adding a 60s buffer guarantees we always catch the terminal status.
    max_polls = (timeout_seconds + 60) // poll_interval
    for attempt in range(max_polls):
        time.sleep(poll_interval)
        result = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        status = result['Status']
        logger.info(f"  [POLL {attempt + 1:02d}] SSM '{label}': [{status.upper()}]")
        if status in ('Success', 'Failed', 'Cancelled', 'TimedOut',
                      'DeliveryTimedOut', 'ExecutionTimedOut'):
            log_fn = logger.info if status == 'Success' else logger.error
            log_fn(f"  [DONE] SSM '{label}' finished with status [{status.upper()}]")
            return {
                'command_id': command_id,
                'status': status,
                'stdout': result.get('StandardOutputContent', '').strip(),
                'stderr': result.get('StandardErrorContent', '').strip()
            }

    logger.warning(f"  [TIMEOUT] Lambda polling timed out for SSM '{label}' after {timeout_seconds}s")
    return {
        'command_id': command_id,
        'status': 'polling_timeout',
        'note': 'Lambda polling timed out; SSM command may still be running on the instance'
    }


def _run_os_update(instance_id):
    """Ensure instance is running, wait for SSM agent, then run apt update and apt upgrade."""
    logger.info(f"--- [CMD 1/4] Ensuring instance {instance_id} is running ---")
    instance_result = _ensure_instance_running(instance_id)

    logger.info("--- [CMD 2/4] Waiting for SSM agent to come online ---")
    ssm_agent_result = _wait_for_ssm_agent(instance_id)

    logger.info("--- [CMD 3/4] Running: apt update -y ---")
    update_result = _run_ssm_command(
        instance_id=instance_id,
        commands=['apt update -y'],
        label='apt-update',
        timeout_seconds=120
    )
    if update_result['status'] != 'Success':
        raise RuntimeError(
            f"apt update failed with status '{update_result['status']}': "
            f"{update_result.get('stderr', '')}"
        )

    logger.info("--- [CMD 4/4] Running: apt upgrade -y ---")
    upgrade_result = _run_ssm_command(
        instance_id=instance_id,
        commands=['DEBIAN_FRONTEND=noninteractive apt upgrade -y'],
        label='apt-upgrade',
        timeout_seconds=600
    )
    if upgrade_result['status'] != 'Success':
        raise RuntimeError(
            f"apt upgrade failed with status '{upgrade_result['status']}': "
            f"{upgrade_result.get('stderr', '')}"
        )

    return {
        'instance': instance_result,
        'ssm_agent': ssm_agent_result,
        'apt_update': update_result,
        'apt_upgrade': upgrade_result
    }


def _run_cert_renew():
    """Ensure Proxy instance is running, wait for SSM agent, then renew the certificate and restart haproxy."""
    logger.info("--- [CMD 1/5] Ensuring Proxy instance is running ---")
    instance_result = _ensure_instance_running(PROXY_INSTANCE_ID)

    logger.info("--- [CMD 2/5] Waiting for SSM agent to come online ---")
    ssm_agent_result = _wait_for_ssm_agent(PROXY_INSTANCE_ID)

    logger.info("--- [CMD 3/5] Running: certbot renew --force-renewal ---")
    certbot_renew_result = _run_ssm_command(
        instance_id=PROXY_INSTANCE_ID,
        commands=['certbot renew --force-renewal'],
        label='certbot-renew',
        timeout_seconds=600
    )
    if certbot_renew_result['status'] != 'Success':
        raise RuntimeError(
            f"certbot renew failed with status '{certbot_renew_result['status']}': "
            f"{certbot_renew_result.get('stderr', '')}"
        )

    logger.info(f"--- [CMD 4/5] Running: certificate bundle for {PROXY_DOMAIN} ---")
    cert_bundle_result = _run_ssm_command(
        instance_id=PROXY_INSTANCE_ID,
        commands=[
            f"bash -c 'cat /etc/letsencrypt/live/{PROXY_DOMAIN}/fullchain.pem "
            f"/etc/letsencrypt/live/{PROXY_DOMAIN}/privkey.pem > "
            f"/etc/haproxy/certs/{PROXY_DOMAIN}.pem'"
        ],
        label='cert-bundle',
        timeout_seconds=30
    )
    if cert_bundle_result['status'] != 'Success':
        raise RuntimeError(
            f"cert bundle failed with status '{cert_bundle_result['status']}': "
            f"{cert_bundle_result.get('stderr', '')}"
        )

    logger.info("--- [CMD 5/5] Running: systemctl restart haproxy ---")
    haproxy_restart_result = _run_ssm_command(
        instance_id=PROXY_INSTANCE_ID,
        commands=['systemctl restart haproxy'],
        label='haproxy-restart',
        timeout_seconds=30
    )
    if haproxy_restart_result['status'] != 'Success':
        raise RuntimeError(
            f"haproxy restart failed with status '{haproxy_restart_result['status']}': "
            f"{haproxy_restart_result.get('stderr', '')}"
        )

    return {
        'instance': instance_result,
        'ssm_agent': ssm_agent_result,
        'certbot_renew': certbot_renew_result,
        'cert_bundle': cert_bundle_result,
        'haproxy_restart': haproxy_restart_result
    }


# ---------------------------------------------------------------------------
# Shared teardown helpers (accept instance_id parameter)
# ---------------------------------------------------------------------------

def _stop_instance(instance_id):
    """Stop the given instance (fire-and-forget; does not wait for stopped state)."""
    logger.info(f"  Querying state of instance {instance_id}")
    response = ec2.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    logger.info(f"  Current state: [{state.upper()}]")

    if state in ('stopped', 'stopping'):
        logger.info(f"  [SKIP] Instance is already {state}, no action needed")
        return {'action': 'already_stopped_or_stopping'}

    if state in ('terminated', 'shutting-down'):
        logger.info(f"  [SKIP] Instance is in terminal state '{state}', cannot stop")
        return {'action': 'skipped', 'reason': state}

    ec2.stop_instances(InstanceIds=[instance_id])
    logger.info(f"  [STOP] Stop signal sent to instance {instance_id}")
    return {'action': 'stopping'}


def _disassociate_iam_instance_profile(instance_id):
    """Remove any active IAM instance profile association from the given instance."""
    logger.info(f"  Checking IAM instance profile associations on {instance_id}")
    assoc_response = ec2.describe_iam_instance_profile_associations(
        Filters=[{'Name': 'instance-id', 'Values': [instance_id]}]
    )
    active = [
        a for a in assoc_response.get('IamInstanceProfileAssociations', [])
        if a.get('State') in ('associated', 'associating')
    ]

    if not active:
        logger.info(f"  [SKIP] No active instance profile found on {instance_id}")
        return {'action': 'skipped', 'reason': 'no_association'}

    association_id = active[0]['AssociationId']
    profile_name = active[0].get('IamInstanceProfile', {}).get('Arn', '').split('/')[-1]
    ec2.disassociate_iam_instance_profile(AssociationId=association_id)
    logger.info(f"  [REMOVE] Disassociated profile '{profile_name}' (id={association_id}) from {instance_id}")
    return {'action': 'disassociated', 'association_id': association_id}


def _remove_maintenance_sg(instance_id):
    """Remove MAINTENANCE_SG_ID from the given instance's security groups."""
    logger.info(f"  Checking security groups on {instance_id}")
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    current_sg_ids = [sg['GroupId'] for sg in instance['SecurityGroups']]
    logger.info(f"  Current SGs: {current_sg_ids}")

    if MAINTENANCE_SG_ID not in current_sg_ids:
        logger.info(f"  [SKIP] Maintenance SG {MAINTENANCE_SG_ID} not found on {instance_id}")
        return {'action': 'skipped', 'reason': 'not_attached'}

    updated_sg_ids = [sg_id for sg_id in current_sg_ids if sg_id != MAINTENANCE_SG_ID]
    ec2.modify_instance_attribute(
        InstanceId=instance_id,
        Groups=updated_sg_ids
    )
    logger.info(f"  [REMOVE] Maintenance SG {MAINTENANCE_SG_ID} removed; remaining SGs: {updated_sg_ids}")
    return {'action': 'removed', 'security_group_id': MAINTENANCE_SG_ID}


def _close_nacl_rules():
    """Delete the NACL entries that were added by _open_nacl_rules."""
    logger.info(f"  Fetching current NACL entries for {PUBLIC_NACL_ID}")
    response = ec2.describe_network_acls(NetworkAclIds=[PUBLIC_NACL_ID])
    entries = response['NetworkAcls'][0]['Entries']

    deleted   = []
    not_found = []

    for rule in INBOUND_RULES:
        matched = next(
            (e for e in entries
             if not e.get('Egress')
             and e.get('Protocol') == rule['protocol']
             and e.get('CidrBlock') == '0.0.0.0/0'
             and e.get('RuleAction') == 'allow'
             and e.get('PortRange', {}).get('From') == rule['from_port']
             and e.get('PortRange', {}).get('To') == rule['to_port']),
            None
        )
        if matched:
            ec2.delete_network_acl_entry(
                NetworkAclId=PUBLIC_NACL_ID,
                RuleNumber=matched['RuleNumber'],
                Egress=False
            )
            logger.info(f"  [DEL ] Inbound NACL rule #{matched['RuleNumber']} removed: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            deleted.append(f"inbound-{rule['description']}")
        else:
            logger.info(f"  [SKIP] Inbound NACL rule not found for cleanup: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            not_found.append(f"inbound-{rule['description']}")

    for rule in OUTBOUND_RULES:
        matched = next(
            (e for e in entries
             if e.get('Egress')
             and e.get('Protocol') == rule['protocol']
             and e.get('CidrBlock') == '0.0.0.0/0'
             and e.get('RuleAction') == 'allow'
             and e.get('PortRange', {}).get('From') == rule['from_port']
             and e.get('PortRange', {}).get('To') == rule['to_port']),
            None
        )
        if matched:
            ec2.delete_network_acl_entry(
                NetworkAclId=PUBLIC_NACL_ID,
                RuleNumber=matched['RuleNumber'],
                Egress=True
            )
            logger.info(f"  [DEL ] Outbound NACL rule #{matched['RuleNumber']} removed: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            deleted.append(f"outbound-{rule['description']}")
        else:
            logger.info(f"  [SKIP] Outbound NACL rule not found for cleanup: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            not_found.append(f"outbound-{rule['description']}")

    logger.info(f"  NACL close summary: {len(deleted)} rule(s) deleted, {len(not_found)} not found")
    return {'deleted': deleted, 'not_found': not_found}


# ---------------------------------------------------------------------------
# Owncast-specific Route Table and NACL helpers
# ---------------------------------------------------------------------------

def _add_route_to_igw():
    """Add a 0.0.0.0/0 -> Internet Gateway route to the Private Subnet Route Table."""
    logger.info(f"  Checking routes on route table {PRIVATE_ROUTE_TABLE_ID}")
    response = ec2.describe_route_tables(RouteTableIds=[PRIVATE_ROUTE_TABLE_ID])
    routes = response['RouteTables'][0]['Routes']

    existing = next(
        (r for r in routes
         if r.get('DestinationCidrBlock') == '0.0.0.0/0'
         and r.get('GatewayId') == INTERNET_GATEWAY_ID),
        None
    )
    if existing:
        logger.info(f"  [SKIP] IGW route 0.0.0.0/0 -> {INTERNET_GATEWAY_ID} already exists")
        return {'action': 'skipped', 'reason': 'already_exists'}

    ec2.create_route(
        RouteTableId=PRIVATE_ROUTE_TABLE_ID,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=INTERNET_GATEWAY_ID
    )
    logger.info(f"  [ADD ] Route 0.0.0.0/0 -> {INTERNET_GATEWAY_ID} added to {PRIVATE_ROUTE_TABLE_ID}")
    return {'action': 'added', 'destination': '0.0.0.0/0', 'gateway': INTERNET_GATEWAY_ID}


def _remove_route_to_igw():
    """Remove the 0.0.0.0/0 -> Internet Gateway route from the Private Subnet Route Table."""
    logger.info(f"  Checking routes on route table {PRIVATE_ROUTE_TABLE_ID}")
    response = ec2.describe_route_tables(RouteTableIds=[PRIVATE_ROUTE_TABLE_ID])
    routes = response['RouteTables'][0]['Routes']

    existing = next(
        (r for r in routes
         if r.get('DestinationCidrBlock') == '0.0.0.0/0'
         and r.get('GatewayId') == INTERNET_GATEWAY_ID),
        None
    )
    if not existing:
        logger.info(f"  [SKIP] IGW route 0.0.0.0/0 -> {INTERNET_GATEWAY_ID} not found, nothing to remove")
        return {'action': 'skipped', 'reason': 'not_found'}

    ec2.delete_route(
        RouteTableId=PRIVATE_ROUTE_TABLE_ID,
        DestinationCidrBlock='0.0.0.0/0'
    )
    logger.info(f"  [DEL ] Route 0.0.0.0/0 -> {INTERNET_GATEWAY_ID} removed from {PRIVATE_ROUTE_TABLE_ID}")
    return {'action': 'removed', 'destination': '0.0.0.0/0', 'gateway': INTERNET_GATEWAY_ID}


def _open_owncast_nacl_rules():
    """Add temporary NACL rules to the Private Subnet NACL for Owncast maintenance."""
    logger.info(f"  Fetching current NACL entries for {PRIVATE_NACL_ID}")
    response = ec2.describe_network_acls(NetworkAclIds=[PRIVATE_NACL_ID])
    entries = response['NetworkAcls'][0]['Entries']

    added   = []
    skipped = []

    next_inbound = _next_rule_number(entries, egress=False)
    for rule in OWNCAST_INBOUND_RULES:
        if _nacl_allow_rule_exists(entries, False, rule['from_port'], rule['to_port'], rule['protocol']):
            logger.info(f"  [SKIP] Inbound rule already exists: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            skipped.append(f"inbound-{rule['description']}")
            continue
        ec2.create_network_acl_entry(
            NetworkAclId=PRIVATE_NACL_ID, RuleNumber=next_inbound,
            Protocol=rule['protocol'], RuleAction='allow', Egress=False,
            CidrBlock='0.0.0.0/0', PortRange={'From': rule['from_port'], 'To': rule['to_port']}
        )
        logger.info(f"  [ADD ] Inbound NACL rule #{next_inbound}: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
        added.append(f"inbound-{rule['description']}")
        next_inbound += 1

    next_outbound = _next_rule_number(entries, egress=True)
    for rule in OWNCAST_OUTBOUND_RULES:
        if _nacl_allow_rule_exists(entries, True, rule['from_port'], rule['to_port'], rule['protocol']):
            logger.info(f"  [SKIP] Outbound rule already exists: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            skipped.append(f"outbound-{rule['description']}")
            continue
        ec2.create_network_acl_entry(
            NetworkAclId=PRIVATE_NACL_ID, RuleNumber=next_outbound,
            Protocol=rule['protocol'], RuleAction='allow', Egress=True,
            CidrBlock='0.0.0.0/0', PortRange={'From': rule['from_port'], 'To': rule['to_port']}
        )
        logger.info(f"  [ADD ] Outbound NACL rule #{next_outbound}: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
        added.append(f"outbound-{rule['description']}")
        next_outbound += 1

    logger.info(f"  NACL open summary: {len(added)} rule(s) added, {len(skipped)} skipped")
    return {'added': added, 'skipped': skipped}


def _associate_elastic_ip():
    """Associate ELASTIC_IP_ALLOC_ID with the Owncast instance.
    Required because the Owncast instance is in a private subnet and needs a
    public IP so the Internet Gateway can NAT outbound traffic to SSM endpoints
    and apt package servers."""
    logger.info(f"  Checking current association of Elastic IP allocation {ELASTIC_IP_ALLOC_ID}")
    response = ec2.describe_addresses(AllocationIds=[ELASTIC_IP_ALLOC_ID])
    address = response['Addresses'][0]
    public_ip = address.get('PublicIp', 'unknown')

    current_instance = address.get('InstanceId')
    if current_instance == OWNCAST_INSTANCE_ID:
        logger.info(f"  [SKIP] Elastic IP {public_ip} already associated with {OWNCAST_INSTANCE_ID}")
        return {'action': 'skipped', 'reason': 'already_associated', 'public_ip': public_ip}

    # If currently associated with another resource, disassociate first
    assoc_id = address.get('AssociationId')
    if assoc_id:
        ec2.disassociate_address(AssociationId=assoc_id)
        logger.info(f"  [DETACH] Elastic IP {public_ip} disassociated from previous resource")

    ec2.associate_address(
        InstanceId=OWNCAST_INSTANCE_ID,
        AllocationId=ELASTIC_IP_ALLOC_ID
    )
    logger.info(f"  [ADD ] Elastic IP {public_ip} ({ELASTIC_IP_ALLOC_ID}) associated with {OWNCAST_INSTANCE_ID}")
    return {'action': 'associated', 'allocation_id': ELASTIC_IP_ALLOC_ID, 'public_ip': public_ip}


def _disassociate_elastic_ip():
    """Disassociate ELASTIC_IP_ALLOC_ID from whatever instance it is currently on."""
    logger.info(f"  Checking current association of Elastic IP allocation {ELASTIC_IP_ALLOC_ID}")
    response = ec2.describe_addresses(AllocationIds=[ELASTIC_IP_ALLOC_ID])
    address = response['Addresses'][0]
    public_ip = address.get('PublicIp', 'unknown')

    assoc_id = address.get('AssociationId')
    if not assoc_id:
        logger.info(f"  [SKIP] Elastic IP {public_ip} is not currently associated")
        return {'action': 'skipped', 'reason': 'not_associated', 'public_ip': public_ip}

    ec2.disassociate_address(AssociationId=assoc_id)
    logger.info(f"  [REMOVE] Elastic IP {public_ip} ({ELASTIC_IP_ALLOC_ID}) disassociated")
    return {'action': 'disassociated', 'allocation_id': ELASTIC_IP_ALLOC_ID, 'public_ip': public_ip}


def _close_owncast_nacl_rules():
    """Delete the NACL entries that were added by _open_owncast_nacl_rules."""
    logger.info(f"  Fetching current NACL entries for {PRIVATE_NACL_ID}")
    response = ec2.describe_network_acls(NetworkAclIds=[PRIVATE_NACL_ID])
    entries = response['NetworkAcls'][0]['Entries']

    deleted   = []
    not_found = []

    for rule in OWNCAST_INBOUND_RULES:
        matched = next(
            (e for e in entries if not e.get('Egress')
             and e.get('Protocol') == rule['protocol'] and e.get('CidrBlock') == '0.0.0.0/0'
             and e.get('RuleAction') == 'allow'
             and e.get('PortRange', {}).get('From') == rule['from_port']
             and e.get('PortRange', {}).get('To') == rule['to_port']), None
        )
        if matched:
            ec2.delete_network_acl_entry(NetworkAclId=PRIVATE_NACL_ID, RuleNumber=matched['RuleNumber'], Egress=False)
            logger.info(f"  [DEL ] Inbound NACL rule #{matched['RuleNumber']} removed: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            deleted.append(f"inbound-{rule['description']}")
        else:
            logger.info(f"  [SKIP] Inbound NACL rule not found for cleanup: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            not_found.append(f"inbound-{rule['description']}")

    for rule in OWNCAST_OUTBOUND_RULES:
        matched = next(
            (e for e in entries if e.get('Egress')
             and e.get('Protocol') == rule['protocol'] and e.get('CidrBlock') == '0.0.0.0/0'
             and e.get('RuleAction') == 'allow'
             and e.get('PortRange', {}).get('From') == rule['from_port']
             and e.get('PortRange', {}).get('To') == rule['to_port']), None
        )
        if matched:
            ec2.delete_network_acl_entry(NetworkAclId=PRIVATE_NACL_ID, RuleNumber=matched['RuleNumber'], Egress=True)
            logger.info(f"  [DEL ] Outbound NACL rule #{matched['RuleNumber']} removed: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            deleted.append(f"outbound-{rule['description']}")
        else:
            logger.info(f"  [SKIP] Outbound NACL rule not found for cleanup: {rule['description']} (port {rule['from_port']}-{rule['to_port']})")
            not_found.append(f"outbound-{rule['description']}")

    logger.info(f"  NACL close summary: {len(deleted)} rule(s) deleted, {len(not_found)} not found")
    return {'deleted': deleted, 'not_found': not_found}
