from finances import get_refundEventList, parse_refund
from datetime import datetime, timezone, timedelta

def main():

    startDate = (((datetime(2023,8, 1)).replace(hour=0, minute=0, second=0, microsecond=0)).astimezone(timezone.utc)).isoformat()
    endDate = ((datetime(2023,9,15)).astimezone(timezone.utc)).isoformat()

    resi = []
    refundEventList = get_refundEventList(startDate, endDate)
    for refund in refundEventList:
        resi.append(parse_refund(refund))  

if __name__ == "__main__":
    main()
