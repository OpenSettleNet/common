from opensettlenet_common.utils import (
    get_hostname,
    get_host_ip,
    sip_headers_to_dict,
    generate_200_ok_response,
)


def test_get_hostname(mocker):
    mocker.patch("socket.gethostname", return_value="test_hostname")
    hostname = get_hostname()
    assert hostname == "test_hostname"


def test_get_host_ip(mocker):
    mocker.patch("socket.gethostname", return_value="localhost")
    mocker.patch(
        "socket.gethostbyname",
        side_effect=lambda hostname: "127.0.0.1"
        if hostname == "localhost"
        else "1.0.0.721",
    )
    ip = get_host_ip()
    assert ip == "127.0.0.1"


def test_sip_headers_to_dict(shared_datadir):
    with open(shared_datadir / "sip" / "ACK.bin", "rb") as fh:
        headers = sip_headers_to_dict(fh.read().decode("utf-8"))
        assert headers == {
            "Via": "SIP/2.0/UDP here.com:5060;branch=z9hG4bKnashds8",
            "Max-Forwards": "70",
            "From": '"User1" <sip:user1@here.com>;tag=1928301774',
            "To": "<sip:user2@there.com>;tag=a6c85cf",
            "Call-ID": "a84b4c76e66710",
            "CSeq": "314159 ACK",
            "Content-Length": "0",
        }

    with open(shared_datadir / "sip" / "INVITE.bin", "rb") as fh:
        headers = sip_headers_to_dict(fh.read().decode("utf-8"))
        assert headers == {
            "Via": "SIP/2.0/UDP here.com:5060;branch=z9hG4bKnashds8",
            "Max-Forwards": "70",
            "To": "<sip:user2@there.com>",
            "From": '"User1" <sip:user1@here.com>;tag=1928301774',
            "Call-ID": "a84b4c76e66710",
            "CSeq": "314159 INVITE",
            "Contact": "<sip:user1@here.com>",
            "Content-Type": "application/sdp",
            "Content-Length": "150",
        }


def test_generate_200_ok_response(shared_datadir):
    with open(shared_datadir / "sip" / "ACK.bin", "rb") as fh:
        packet = fh.read().decode("utf-8")
        assert generate_200_ok_response(packet) == (
            "SIP/2.0 200 OK\r\n"
            "Via: SIP/2.0/UDP here.com:5060;branch=z9hG4bKnashds8\r\n"
            'From: "User1" <sip:user1@here.com>;tag=1928301774\r\n'
            "To: <sip:user2@there.com>;tag=a6c85cf\r\n"
            "Call-ID: a84b4c76e66710\r\n"
            "CSeq: 314159 NOTIFY\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )
