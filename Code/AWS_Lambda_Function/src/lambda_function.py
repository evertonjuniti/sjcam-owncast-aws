import datetime
import rsa
import boto3
from botocore.exceptions import ClientError
import os
import urllib.parse
import json
import re
import logging
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

s3 = boto3.client('s3')
region = os.environ['REGION']
secrets_client = boto3.client('secretsmanager', region_name=region)
PRIVATE_KEY_CACHE = None
BUCKET = os.environ['BUCKET_NAME']
PREFIX = os.environ['FOLDER_PREFIX']
EXPIRES_IN = os.environ['EXPIRES_IN']

def get_allowed_emails():
    secret_name = os.environ['ALLOWED_EMAILS_SECRET']
    try:
        resp = secrets_client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error("Error reading email secret: " + str(e))
        raise
    emails = json.loads(resp['SecretString'])
    return {e.lower() for e in emails}

ALLOWED_EMAILS = get_allowed_emails()

def lambda_handler(event, context):
    method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    raw_path = event.get('path') or event.get('rawPath', '')

    if method == 'GET' and raw_path == '/instance':
        return handle_instance_status(event)

    if method == 'PUT' and raw_path == '/instance/turnoff':
        return handle_turn_off_instance(event)

    if method == 'PUT' and raw_path == '/instance/turnon':
        return handle_turn_on_instance(event)

    if method == 'GET' and raw_path == '/list-videos':
        return handle_list_videos(event)

    if method == 'GET' and raw_path == '/auth-cookies':
        return handle_auth_cookies(event)

    if method == 'GET' and raw_path.startswith('/playlist/'):
        return handle_playlist(event)
    
    logger.warning(f"Method | route not found: {method} | {raw_path}", exc_info=True)
    return {
        "statusCode": 404,
        "headers": _cors_headers(),
        "body": json.dumps({"error": "Internal Server Error"})
    }

def handle_instance_status(event):
    try:
        auth_result = validate_authorization(event)
        if auth_result is not None:
            return auth_result

        ec2 = boto3.client('ec2')
        instance_id = os.environ['EC2_INSTANCE_ID']
        response = ec2.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps({"status": state})
        }
    except Exception as e:
        logger.error(f"Error getting EC2 instance status: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": "Internal Server Error"})
        }

def handle_turn_off_instance(event):
    try:
        auth_result = validate_authorization(event)
        if auth_result is not None:
            return auth_result

        ec2 = boto3.client('ec2')
        instance_id = os.environ['EC2_INSTANCE_ID']
        ec2.stop_instances(InstanceIds=[instance_id])
        
        instance_proxy_id = os.environ['EC2_INSTANCE_PROXY_ID']
        ec2.stop_instances(InstanceIds=[instance_proxy_id])
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps({"action": "stopping"})
        }
    except Exception as e:
        logger.error(f"Error shutting down EC2 instance: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": "Internal Server Error"})
        }

def handle_turn_on_instance(event):
    try:
        auth_result = validate_authorization(event)
        if auth_result is not None:
            return auth_result

        ec2 = boto3.client('ec2')
        instance_id = os.environ['EC2_INSTANCE_ID']
        ec2.start_instances(InstanceIds=[instance_id])
        
        instance_proxy_id = os.environ['EC2_INSTANCE_PROXY_ID']
        ec2.start_instances(InstanceIds=[instance_proxy_id])
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps({"action": "starting"})
        }
    except Exception as e:
        logger.error(f"Error turning on the EC2 instance: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": "Internal Server Error"})
        }

def handle_list_videos(event):
    try:
        auth_result = validate_authorization(event)
        if auth_result is not None:
            return auth_result

        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET, Prefix=PREFIX)

        videos = []
        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                if not key.endswith('-0.ts'):
                    continue

                match = re.match(rf"{PREFIX}stream-(.+?)-0\.ts$", key)
                if match:
                    videos.append({
                        "videoId": match.group(1),
                        "timestamp": obj['LastModified']
                    })

        videos.sort(key=lambda x: x['timestamp'], reverse=True)

        body = [
            {
                "videoId": v["videoId"],
                "dateTime": f"{v['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {v['videoId']}"
            }
            for v in videos
        ]
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(body)
        }

    except Exception as e:
        logger.error(f"Error when handling list of videos: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": "Internal Server Error"})
        }

def handle_auth_cookies(event):
    auth_result = validate_authorization(event)
    if auth_result is not None:
        return auth_result

    cookies = sign_cookies()

    set_ck = []
    for k in ['CloudFront-Policy','CloudFront-Signature','CloudFront-Key-Pair-Id']:
        set_ck.append(f"{k}={cookies[k]};Path=/;Domain={os.environ['COOKIE_DOMAIN']};Secure;HttpOnly;SameSite=None")

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "multiValueHeaders": {
            "Set-Cookie": set_ck
        },
        "body": ""
    }

def handle_playlist(event):
    try:
        auth_result = validate_authorization(event)
        if auth_result is not None:
            return auth_result
        
        video_id = urllib.parse.unquote(event['pathParameters']['video_id'])
        
        domain = os.environ['ORIGIN_DOMAIN']

        if (video_id == 'stream.m3u8'):
            key_live = f"{PREFIX}stream.m3u8"
            try:
                resp = s3.get_object(Bucket=BUCKET, Key=key_live)
                raw = resp['Body'].read().decode('utf-8')
                raw = raw.replace('#EXT-X-ENDLIST', '')
                base_url = f"{domain}/{PREFIX}"
                lines = raw.splitlines()

                processed = []
                for ln in lines:
                    if ln.strip() and not ln.startswith('#'):
                        processed.append(f"{base_url}{ln}")
                    else:
                        processed.append(ln)
                playlist = "\n".join(processed)
                
                return {
                    "statusCode": 200,
                    "headers": _cors_headers_get_mpegurl(),
                    "body": playlist
                }
            except ClientError:
                pass

        if video_id.endswith('.m3u8'):
            video_id = video_id.replace('.m3u8', '')

        prefix_match = f"{PREFIX}stream-{video_id}-"

        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET, Prefix=prefix_match)

        segments = []
        for page in pages:
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.ts'):
                    segments.append(obj['Key'])

        segments.sort(key=lambda k: int(re.search(rf"{prefix_match}([0-9]+)\.ts$", k).group(1)))

        if not segments:
            logger.error(f"Video {video_id} not found", exc_info=True)
            return {
                "statusCode": 500,
                "headers": _cors_headers(),
                "body": json.dumps({"error": "Internal Server Error"})
            }

        playlist = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n"
        playlist += "#EXT-X-MEDIA-SEQUENCE:0\n"

        for key in segments:
            filename = key.split("/")[-1]
            absolute = f"{domain}/{PREFIX}{filename}"
            playlist += "#EXTINF:6.000,\n" + absolute + "\n"

        playlist += "#EXT-X-ENDLIST"

        return {
            "statusCode": 200,
            "headers": _cors_headers_get_mpegurl(),
            "body": playlist
        }

    except Exception as e:
        logger.error(f"Error when handling playlist: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": "Internal Server Error"})
        }

def validate_authorization(event):
    try:
        claims = (
            event.get("requestContext", {})
                 .get("authorizer", {})
                 .get("claims", {})
        )
        if not claims:
            logger.warning(f"Request without authentication context (missing claims)", exc_info=True)
            return _unauthorized()

        user_email = (claims.get("email") or claims.get("cognito:username") or "").strip().lower()
        if not user_email:
            logger.warning(f"User email missing from token", exc_info=True)
            return _unauthorized()

        if ALLOWED_EMAILS and user_email not in ALLOWED_EMAILS:
            logger.warning(f"Access denied: Unauthorized email", exc_info=True)
            return _unauthorized()

        return None
    except Exception as e:
        logger.error(f"Error validating authorization: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": _cors_headers(),
            "body": json.dumps({"error": "Internal Server Error"})
        }
    
def _unauthorized():
    return {
        "statusCode": 401,
        "headers": _cors_headers(),
        "body": json.dumps({"Unauthorized"})
    }

def _cors_headers_get_mpegurl():
    return {
        "Access-Control-Allow-Origin": f"{os.environ['ORIGIN_DOMAIN']}",
        "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true",
        "Content-Type": "application/vnd.apple.mpegurl"
    }

def _cors_headers():
    return {
        "Access-Control-Allow-Origin": f"{os.environ['ORIGIN_DOMAIN']}",
        "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true",
        "Content-Type": "application/json"
    }

secrets_client = boto3.client('secretsmanager')

def get_private_key():
    global PRIVATE_KEY_CACHE
    if PRIVATE_KEY_CACHE is None:
        secret = secrets_client.get_secret_value(SecretId=os.environ['SECRETS_NAME'])
        PRIVATE_KEY_CACHE = rsa.PrivateKey.load_pkcs1(secret['SecretString'].encode('utf-8'))
    return PRIVATE_KEY_CACHE

def _cf_b64url(data: bytes) -> str:
    b64 = base64.b64encode(data).decode('utf-8')
    return b64.replace('+', '-').replace('/', '~').replace('=', '_')

def _generate_cf_cookie(policy: str, key_id: str, rsa_signer) -> dict:
    policy_bytes = policy.encode('utf-8')
    signature = rsa_signer(policy_bytes)
    return {
        'CloudFront-Policy': _cf_b64url(policy_bytes),
        'CloudFront-Signature': _cf_b64url(signature),
        'CloudFront-Key-Pair-Id': key_id,
    }

def sign_cookies():
    key_id   = os.environ['CF_KEY_PAIR_ID']
    priv_key = get_private_key()
    expire   = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

    policy = {
      "Statement": [{
        "Resource": f"{os.environ['ORIGIN_DOMAIN']}/{PREFIX}*",
        "Condition": { "DateLessThan": {"AWS:EpochTime": int(expire.timestamp())} }
      }]
    }

    return _generate_cf_cookie(
        policy=json.dumps(policy, separators=(",",":")),
        key_id=key_id,
        rsa_signer=lambda msg: rsa.sign(msg, priv_key, 'SHA-1')
    )
