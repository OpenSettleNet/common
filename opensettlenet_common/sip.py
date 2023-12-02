import abc
import functools
import inspect
import re
import secrets
import socket
import urllib.parse
from typing import Callable, Dict, Optional, Set, Union

import attrs
import xmltodict
from scapy.layers.inet import IP, UDP  # type: ignore
from scapy.packet import Raw  # type: ignore
from scapy.sendrecv import send  # type: ignore

from opensettlenet_common import utils
from opensettlenet_common.config import settings


class Header:
    @staticmethod
    def header(name: str, priority: Optional[int] = None) -> Callable:
        def _header(method: Callable) -> Callable:
            method_returns = inspect.signature(method).return_annotation
            if method_returns != str and method_returns != Optional[str]:
                raise ValueError(
                    f"Cannot define a method for header {name} returning a type "
                    f"other than `str`, `None`, or `Optional[str]`"
                )

            @functools.wraps(method)
            def _method(*args, **kwargs):
                return_value = method(*args, **kwargs)
                if type(return_value) not in (str, type(None)):
                    raise ValueError(
                        f"Method for header {name} returned {return_value} of type {type(return_value)}, "
                        f"which is neither `str` nor `None`"
                    )
                return return_value

            _method._header_name = name  # type: ignore
            _method._header_priority = priority  # type: ignore
            return _method

        return _header

    @classmethod
    def _get_headers(cls, instance: object) -> Dict[str, Optional[str]]:
        headers = [
            header
            for (_, header) in inspect.getmembers(instance, predicate=inspect.ismethod)
            if getattr(header, "_header_name", None)
        ]
        headers.sort(
            key=lambda header: header._header_priority  # type: ignore
            if header._header_priority is not None  # type: ignore
            else float("inf")
        )
        return {header._header_name: header() for header in headers}  # type: ignore

    @classmethod
    def get_headers(cls, instance: object) -> Dict[str, str]:
        return {
            header: value
            for header, value in cls._get_headers(instance).items()
            if value is not None
        }


@attrs.define(kw_only=True)
class SIPURI:
    PATTERN = re.compile(
        r"^(?:sip:)?"  # Optional "sip:" scheme
        r"(?:([^@;:>]+)@)?"  # Optional user
        r"([^@;:]+)"  # Domain
        r"(?:[:]([0-9]+))?"  # Optional port
        r"(;.*)?$"  # Optional parameters
    )

    domain: str
    user: Optional[str] = None
    port: Optional[int] = attrs.field(
        default=5060,
        validator=attrs.validators.and_(
            attrs.validators.ge(0), attrs.validators.le(65535)
        ),
    )
    parameters: Set[str] = attrs.field(factory=set)

    def __str__(self) -> str:
        uri = self.domain
        if self.port is not None:
            uri = f"{urllib.parse.quote(uri)}:{self.port}"
        if self.user is not None:
            uri = f"{urllib.parse.quote(self.user)}@{uri}"
        if self.parameters:
            parameters = ";".join(self.parameters)
            uri = f"{uri};{parameters}"
        return f"sip:{uri}"

    def for_start_line(self) -> str:
        uri = self.domain
        if self.user is not None:
            uri = f"{urllib.parse.quote(self.user)}@{uri}"
        return f"sip:{uri}"

    def get_domain(self) -> str:
        return self.domain

    def get_port(self) -> int:
        return self.port if self.port is not None else 5060

    def get_user(self) -> Optional[str]:
        return self.user

    def add_parameter(self, parameter: str):
        self.parameters.add(parameter)

    @classmethod
    def from_uri(cls, uri: str) -> "SIPURI":
        match = cls.PATTERN.match(uri)
        if match is None:
            raise ValueError(f"SIP URI {uri!r} does not match pattern {cls.PATTERN}")
        (user, domain, port, packed_parameters) = match.groups()
        return cls(
            domain=domain,
            user=user,
            port=int(port) if port is not None else None,
            parameters={
                parameter for parameter in packed_parameters.split(";") if parameter
            }
            if packed_parameters
            else set(),
        )


@attrs.define(auto_attribs=True, kw_only=True)
class Address:
    PATTERN = re.compile(r"""(?:"(.+)"|.+)\s+<sip:([^>]+)>(;.*)?""")
    sip_uri: SIPURI
    display_name: Optional[str] = None
    parameters: Set[str] = attrs.field(factory=set)

    def __str__(self) -> str:
        address = f"<{self.sip_uri}>"
        if self.display_name is not None:
            address = f'"{self.display_name}" {address}'
        if self.parameters:
            parameters = ";".join(self.parameters)
            address = f"{address};{parameters}"
        return address

    def add_parameter(self, parameter: str):
        self.parameters.add(parameter)

    def add_parameter_to_uri(self, parameter: str):
        self.sip_uri.add_parameter(parameter)

    @classmethod
    def from_address(cls, address: str) -> "Address":
        match = cls.PATTERN.match(address)
        if match:
            display_name, uri, packed_parameters = match.groups()
        else:
            uri = address  # Hopefully.
            display_name, packed_parameters = None, None
        return cls(
            display_name=display_name,
            sip_uri=SIPURI.from_uri(uri),
            parameters={
                parameter for parameter in packed_parameters.split(";") if parameter
            }
            if packed_parameters
            else set(),
        )


@attrs.define(auto_attribs=True, kw_only=True)
class SIP(abc.ABC):
    to_field: Address = attrs.field(
        converter=lambda field: Address.from_address(field)
        if not isinstance(field, Address)
        else field
    )
    from_field: Address = attrs.field(
        converter=lambda field: Address.from_address(field)
        if not isinstance(field, Address)
        else field
    )

    call_id: str
    cseq: str
    max_forwards: str
    contact: str = "sip:biller@10.10.0.12:5060"
    accept: Optional[str] = None
    event: Optional[str] = None

    body: Optional[str] = None

    to_tag: Optional[str] = None
    transport_protocol: str = "UDP"

    src_ip: Optional[str] = None
    src_port: Optional[int] = None

    @abc.abstractmethod
    def method(self) -> str:
        pass

    @Header.header("Accept")
    def accept_header(self) -> Optional[str]:
        return self.accept

    @Header.header("Call-ID", priority=4)
    def call_id_header(self) -> str:
        return self.call_id

    @Header.header("Contact")
    def contact_header(self) -> str:
        return self.contact

    @Header.header("Content-Length")
    def content_length_header(self) -> Optional[str]:
        body = self.get_body()
        return str(len(body.encode("utf-8"))) if body is not None else "0"

    @Header.header("Content-Type")
    def content_type_header(self) -> Optional[str]:
        return "application/xml" if self.body is not None else None

    @Header.header("CSeq", priority=3)
    def cseq_header(self) -> str:
        return f"{self.cseq} {self.method()}"

    @Header.header("Event")
    def event_header(self) -> Optional[str]:
        return self.event

    @Header.header("From", priority=2)
    def from_header(self) -> str:
        return str(self.from_field)

    @Header.header("Max-Forwards")
    def max_forwards_header(self) -> str:
        return self.max_forwards

    @Header.header("To", priority=1)
    def to_header(self) -> str:
        return (
            f"{self.to_field};{self.to_tag}"
            if self.to_tag is not None
            else f"{self.to_field}"
        )

    @Header.header("Via", priority=0)
    def via_header(self) -> str:
        return f"SIP/2.0/{self.transport_protocol} {self.get_src_ip()}:{self.get_src_port()}"

    def gen_pidf_xml(self, state="unpaid"):
        pidf = {
            "presence": {
                "@xmlns": "urn:ietf:params:xml:ns:pidf",
                "@entity": self.from_field,
                "tuple": {
                    "@id": state,
                    "status": {"basic": "open"},
                    "contact": {"@priority": "0.8", "#text": str(self.from_field)},
                    "note": [settings.PAYMENT_WALLET, str(0.001)],
                },
            }
        }
        return xmltodict.unparse(pidf, pretty=True)

    def get_body(self) -> Optional[str]:
        return self.body

    def get_headers(self) -> Dict[str, str]:
        return Header.get_headers(self)

    def format_headers(self) -> str:
        return "\r\n".join(
            f"{key}: {value}" for key, value in self.get_headers().items()
        )

    def get_start_line(self) -> str:
        return f"{self.method()} {self.to_field.sip_uri.for_start_line()} SIP/2.0"

    def format(self) -> str:
        start_line = self.get_start_line()
        headers = self.format_headers()
        body = self.get_body()
        if body is not None:
            return f"{start_line}\r\n{headers}\r\n\r\n{body}"
        else:
            return f"{start_line}\r\n{headers}\r\n\r\n"

    def get_host_ip(self) -> str:
        return utils.get_host_ip()

    def get_host_port(self) -> int:
        return 5060

    def get_src_ip(self) -> str:
        return self.src_ip or self.get_host_ip()

    def get_src_port(self) -> int:
        return self.src_port if self.src_port is not None else 5060

    def send_msg(self, ip: Optional[str] = None, port: Optional[int] = None):
        pkt = (
            IP(
                src=self.get_host_ip(),
                dst=ip or socket.gethostbyname(self.to_field.sip_uri.get_domain()),
            )
            / UDP(dport=port or self.to_field.sip_uri.get_port())
            / Raw(load=self.format())
        )
        send(pkt)

    def add_to_tag(self) -> str:
        self.to_tag = secrets.token_hex(10)
        return self.to_tag

    def set_cseq(self, cseq: Union[int, str]):
        self.cseq = str(cseq)

    def increment_cseq(self) -> int:
        cseq = int(self.cseq)
        new_cseq = cseq + 1
        self.cseq = str(new_cseq)
        return new_cseq

    @classmethod
    def from_event(
        cls, event, call_id_override: Optional[str] = None, **kwargs
    ) -> "SIP":
        to_uri = SIPURI.from_uri(event.getHeader("variable_sip_to_uri"))
        to_uri.add_parameter("UDP")
        from_uri = SIPURI(
            user=event.getHeader("variable_sip_from_user"),
            domain=utils.get_host_ip(),
            parameters={"UDP"},
        )

        return cls(
            cseq="1",
            call_id=call_id_override or event.getHeader("variable_sip_call_id"),
            max_forwards="1",
            event="presence",
            from_field=Address(sip_uri=from_uri),
            to_field=Address(sip_uri=to_uri),
            src_ip=event.getHeader("FreeSWITCH-IPv4")
            or None,  # Does .getHeader return None if the key isn't found?
            **kwargs,
        )


@attrs.define(auto_attribs=True, kw_only=True)
class Subscribe(SIP):
    expires: str

    def method(self) -> str:
        return "SUBSCRIBE"

    def get_body(self) -> Optional[str]:
        return None

    @Header.header("Accept")
    def accept_header(self) -> Optional[str]:
        return "application/xml"

    @Header.header("Expires")
    def expires_header(self) -> str:
        return self.expires

    @classmethod
    def from_event(
        cls, event, call_id_override: Optional[str] = None, **kwargs
    ) -> "SIP":
        subscribe = super().from_event(
            event, call_id_override, expires="3600", **kwargs
        )
        subscribe.from_field.add_parameter("tag=1234")  # despise this
        return subscribe


@attrs.define(auto_attribs=True, kw_only=True)
class Publish(SIP):
    def method(self) -> str:
        return "PUBLISH"

    @Header.header("Accept")
    def accept_header(self) -> Optional[str]:
        return "application/xml"

    def get_body(self) -> Optional[str]:
        return super().get_body() or self.gen_pidf_xml()


@attrs.define(auto_attribs=True)
class Notify(SIP):
    subscription_state: Optional[str] = None
    expires: Optional[str] = None

    def method(self) -> str:
        return "NOTIFY"

    @Header.header("Subscription-State")
    def subscription_state_header(self) -> Optional[str]:
        return self.subscription_state

    @Header.header("Expires")
    def expires_header(self) -> Optional[str]:
        return self.expires

    def get_body(self) -> Optional[str]:
        return super().get_body() or self.gen_pidf_xml()
