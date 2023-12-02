import re
import socket
from typing import Dict

HEADER_LINE = re.compile(r"^([a-zA-Z0-9-]+):\s*(.*)$")


def get_hostname() -> str:
    return socket.gethostname()


def get_host_ip() -> str:
    return socket.gethostbyname(get_hostname())


def sip_headers_to_dict(packet) -> Dict[str, str]:
    # All SIP packets contain a double CRLF between the start line / headers & the body (even if it's empty)
    preface, *_ = packet.split("\r\n\r\n")
    # The start line & headers (if there are any) are all separated by CRLFs
    [_, *headers] = preface.split("\r\n")
    header_dict = {}
    for header in headers:
        match = HEADER_LINE.match(header)
        if match is None:
            raise ValueError(f"{header!r} is not a valid SIP header")
        header_key, header_value = match.groups()
        header_dict[header_key] = header_value
    return header_dict


def generate_200_ok_response(packet) -> str:
    headers = sip_headers_to_dict(packet)

    response = (
        f"SIP/2.0 200 OK\r\n"
        f"Via: {headers['Via']}\r\n"
        f"From: {headers['From']}\r\n"
        f"To: {headers['To']}\r\n"
        f"Call-ID: {headers['Call-ID']}\r\n"
        f"CSeq: {headers['CSeq'].split()[0]} NOTIFY\r\n"
        f"Content-Length: 0\r\n\r\n"
    )
    return response
