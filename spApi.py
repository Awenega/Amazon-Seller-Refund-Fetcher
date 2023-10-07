import requests
from datetime import datetime
import hashlib, hmac 
import urllib
import boto3
import json

x_amz_access_token = None
sts_client = None

def load_credentials():
    try:
        with open('credentials.json', 'r') as f:
            credentials = json.load(f)
            return credentials
    except FileNotFoundError:
        print(f"File 'credentials.json not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in credentials.json")
        return None

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def get_access_token(credentials):
    if credentials:
        refresh_token = credentials.get("refresh_token")
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
    else:
        return None
    
    url = "https://api.amazon.com/auth/o2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
    data = {"grant_type": "refresh_token","refresh_token":f"{refresh_token}", "client_id": f"{client_id}", "client_secret": f"{client_secret}"}
    try:
        response = requests.post(url,headers=headers,data=data)
        response.raise_for_status()
        print("Login success")
        return response.json().get("access_token")
    except requests.exceptions.HTTPError as err:
        print(err)
        return None

def get_headers(method,canonical_uri,canonical_querystring,payload_hash=''):
    global x_amz_access_token
    global sts_client
    global assumed_role_object

    credentials = load_credentials()
    aws_access_key_id = credentials.get("aws_access_key_id")
    aws_secret_access_key = credentials.get("aws_secret_access_key")
    RoleArn = credentials.get("RoleArn")

    host = "sellingpartnerapi-eu.amazon.com"
    user_agent = "RequestReport(Language=Python/3.9.9;Platform=Windows/10)"
    
    if x_amz_access_token == None:
        x_amz_access_token = get_access_token(credentials)
    if sts_client == None:
        sts_client = boto3.client('sts', aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key, 
                                region_name="eu-west-1"
                            )

    assumed_role_object=sts_client.assume_role(
        RoleArn=RoleArn,
        RoleSessionName="sp-api"
    )
    access_key = assumed_role_object['Credentials']['AccessKeyId']
    secret_key = assumed_role_object['Credentials']['SecretAccessKey']
    session_token = assumed_role_object['Credentials']['SessionToken']
    tmp = datetime.utcnow()
    x_amz_date = tmp.strftime("%Y%m%dT%H%M%SZ")
    canonical_headers = 'host:' + host + "\n" + "user-agent:" + user_agent + "\n" + "x-amz-access-token:" + x_amz_access_token + "\n" + "x-amz-date:" + x_amz_date + "\n" + "x-amz-security-token:" + session_token
    signed_headers = 'host;user-agent;x-amz-access-token;x-amz-date;x-amz-security-token'
    payload_hash = hashlib.sha256(payload_hash.encode('utf-8')).hexdigest()
    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n\n' + signed_headers + '\n' + payload_hash
    #TASK 2
    datestamp = tmp.strftime('%Y%m%d')
    region = "eu-west-1"
    service = "execute-api"
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  x_amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    # TASK 3
    signing_key = getSignatureKey(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
    # TASK 4
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
    headers = {'x-amz-date':x_amz_date, 'Authorization':authorization_header, 'user-agent':user_agent, 'x-amz-access-token':x_amz_access_token, 'x-amz-security-token': session_token}
    return headers
        
def get_canonical_query_string(request_parameters):
    canonical_query_string = urllib.parse.quote_plus(request_parameters,safe="=&")
    return canonical_query_string

