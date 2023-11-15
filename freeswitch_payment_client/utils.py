# redis://host:port or redis://password@host:port
import re
import socket

CHANNEL_HANGUP = """Event-Name: CHANNEL_HANGUP
Core-UUID: 4a637982-ae30-407b-85e6-7e16f2e6c0d3
FreeSWITCH-Hostname: freeswitch-server.local
FreeSWITCH-Switchname: freeswitch-server
FreeSWITCH-IPv4: 192.168.1.100
FreeSWITCH-IPv6: ::1
Event-Date-Local: 2023-10-05 14:32:18
Event-Date-GMT: Wed, 05 Oct 2023 14:32:18 GMT
Event-Date-Timestamp: 1662445938000000
Event-Calling-File: switch_core_state_machine.c
Event-Calling-Function: switch_core_session_run
Event-Calling-Line-Number: 596
Channel-State: CS_HANGUP
Channel-Call-State: HANGUP
Channel-State-Number: 10
Channel-Name: sofia/internal/1000@192.168.1.100
Unique-ID: 12345678-1234-1234-1234-123456789012
Call-Direction: inbound
Presence-Call-Direction: inbound
Channel-HIT-Dialplan: true
Channel-Presence-ID: 1000@192.168.1.100
Channel-Call-UUID: 12345678-1234-1234-1234-123456789012
Answer-State: hangup
Hangup-Cause: NORMAL_CLEARING
Channel-Read-Codec-Name: PCMU
Channel-Read-Codec-Rate: 8000
Channel-Write-Codec-Name: PCMU
Channel-Write-Codec-Rate: 8000
variable_sip_from_uri: sip:1000@192.168.1.100
variable_sip_from_user: 1000
variable_sip_from_host: 192.168.1.100
variable_sip_to_uri: sip:1001@192.168.1.100
variable_sip_to_user: 1001
variable_sip_to_host: 192.168.1.100
variable_sip_call_id: bc6d585a-6f09-41ae-bb29-2dcd296b2a5e
variable_sip_local_uri: sip:1001@192.168.1.100
variable_sip_allow: INVITE, ACK, BYE, CANCEL, OPTIONS, MESSAGE, UPDATE, INFO, REGISTER, REFER, NOTIFY
variable_sip_cseq: 102 BYE
variable_last_sip_response_num: 200
variable_last_sip_response: OK
"""


def parse_redis_url(url):
    _, host, port = url.split(':')
    try:
        password, host = host.split('@')
    except ValueError:
        return host[2:], int(port), None

    return host, int(port), password[2:]


def get_hostname() -> str:
    return socket.gethostname()


def get_host_ip() -> str:
    return socket.gethostbyname(get_hostname())


def is_200_ok(sip_packet: str) -> bool:
    sip_lines = sip_packet.strip().split("\n")
    if not sip_lines:
        return False
    if "200 OK" in sip_lines[0]:
        return True
    return False


def sip_headers_to_dict(packet) -> dict:
    headers_dict = {}
    headers = packet.split('\r\n')

    for header in headers:
        if ': ' in header:
            key, value = header.split(': ', 1)
            headers_dict[key.strip()] = value.strip()

    return headers_dict


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


def increment_cseq(cseq: str) -> str:
    try:
        number = int(cseq)
        incremented_number = number + 1
        return str(incremented_number)
    except ValueError:
        raise ValueError("Invalid number string provided.")


def generate_to_header(from_header):
    match = re.search(r'<(.*?)>', from_header)
    if match:
        to_value = match.group(1)
    else:
        to_value = from_header.split(";")[0]
    return to_value


def extract_to_user(to_header):
    match = re.search(r'<sip:([^@>]*)', to_header)
    if match:
        to_user = match.group(1)
    else:
        to_user = to_header.split("@", 1)[0].strip()
    to_user = to_user.lstrip("sip:")  # Exclude "sip" prefix if present
    return to_user


def extract_destination_ip(to_header):
    match = re.search(r'@([\d.]+)', to_header)
    if match:
        destination_ip = match.group(1)
    else:
        destination_ip = None
    return destination_ip


def generate_from_header(to_header):
    from_header = "From: {}".format(to_header)
    return from_header


def get_header_value(headers_dict, header_name):
    return next(
        (
            value
            for key, value in headers_dict.items()
            if key.lower() == header_name.lower()
        ),
        None,
    )
