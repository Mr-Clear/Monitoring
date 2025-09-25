import requests

from datetime import datetime
import urllib3.exceptions

from db import DbData

def test_http(url: str) -> list[DbData]:
    host = url.split('/')[2]
    timestamp = datetime.now()
    ret = []
    response = None
    try:
        response = requests.get(url, timeout=10, stream=True)
        ret.append(DbData(host, f'http_status', response.status_code, str(response), timestamp))

        cert = None
        if response.url.startswith('https'):
            conn = getattr(response.raw, 'connection', None)
            sock = getattr(conn, 'sock', None) if conn is not None else None
            if sock and hasattr(sock, 'getpeercert'):
                try:
                    cert = sock.getpeercert()
                    not_after = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                    days = (not_after - timestamp).days
                    ret.append(DbData(host, 'certificate_days_remaining', days, str(cert), timestamp))
                except Exception:
                    ret.append(DbData(host, 'certificate_days_remaining', None, None, timestamp))

    except requests.RequestException as e:
        if e.args and isinstance(e.args[0], urllib3.exceptions.MaxRetryError):
            ret.append(DbData(host, f'http_status', None, str(e.args[0].reason), timestamp))
        else:
            ret.append(DbData(host, f'http_status', None, str(e), timestamp))
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

    return ret
