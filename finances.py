from spApi import get_headers, load_credentials
import requests
import time
import json

MARKETPLACEID_IT = "APJ6JRA9NG5V4"     
MARKETPLACEID_ES = "A1PA6795UKMFR9"     
MARKETPLACEID_DE = "A1RKKUPIHCS9HS"
HOST = "sellingpartnerapi-eu.amazon.com"
   
def handle_response(response, refundEventList):
    if 'payload' not in response:
            print(response)
            return False
    
    if 'FinancialEvents' in response['payload']:
        if 'RefundEventList' in response['payload']['FinancialEvents']:
            for event in response['payload']['FinancialEvents']['RefundEventList']:
                refundEventList.append(event)
    return True
    
def get_refundEventList(startDate, endDate):
    NextToken = None
    i = 0
    refundEventList = []
    while True:
        method = "GET"
        path = "/finances/v0/financialEvents"
        headers = get_headers(method, path, '')

        request_url = "https://" + HOST + path
        if NextToken == None:
            payload = {'PostedAfter': startDate, 'PostedBefore': endDate}
        else:
            payload = {'PostedAfter': startDate, 'PostedBefore': endDate, 'NextToken': NextToken}
        
        print(f"Processing report {i}")
        response = requests.get(url=request_url,headers=headers, params=payload).json()
        with open(f"reso{i}.json", 'w') as f:
            f.write(json.dumps(response))
        ret = handle_response(response, refundEventList)
        if not ret:
            return response
        
        if "NextToken" in response["payload"]:
            NextToken = response["payload"]["NextToken"]
            i += 1
            time.sleep(1)
        else:
            print('No more NextToken')
            break

    return refundEventList

def parse_refund(refund):
    SKUS = load_credentials()['SKUS']
    for elem in refund['ShipmentItemAdjustmentList']:
        reso_json = {'Refund' : {}}
        refund_json = reso_json['Refund']
        refund_json['order_id'] = refund['AmazonOrderId']
        refund_json['purchase_date'] = refund['PostedDate']
        refund_json['sales_channel'] = refund['MarketplaceName']
        refund_json['asin'] = SKUS[elem['SellerSKU']]
        refund_json['quantity'] = elem['QuantityShipped']
        refund_json['comm_venditore'], refund_json['comm_refund'] = 0.0, 0.0
        if 'ItemFeeAdjustmentList' in elem:
            for fee in elem['ItemFeeAdjustmentList']:
                if fee['FeeType'] == 'Commission':
                    refund_json['comm_venditore'] = fee['FeeAmount']['CurrencyAmount']
                if fee['FeeType'] == 'RefundCommission':
                    refund_json['comm_refund'] = fee['FeeAmount']['CurrencyAmount']
            if refund_json['comm_venditore'] != 0.0 and refund_json['comm_refund'] != 0.0:
                return reso_json