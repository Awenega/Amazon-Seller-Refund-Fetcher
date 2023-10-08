from finances import get_refundEventList, parse_refund
from datetime import datetime, timezone, timedelta
import requests
import json

def main():

    startDate = (((datetime(2023,7, 3)).replace(hour=0, minute=0, second=0, microsecond=0)).astimezone(timezone.utc)).isoformat()
    endDate = ((datetime(2023,10,1)).astimezone(timezone.utc)).isoformat()

    refunds = []
    refundEventList = get_refundEventList(startDate, endDate)
    for refundEvent in refundEventList:
        refund = parse_refund(refundEvent)
        if refund is not None:
            refunds.append(refund)

if __name__ == "__main__":
    main()
