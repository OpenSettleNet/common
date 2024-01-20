import pytest

from opensettlenet_common.sip import SIPURI, Address, SIP


class TestSIPURI:
    valid_uri = "sip:user@domain.com:5060;param1=value1;param2=value2"
    valid_uri_no_user = "sip:domain.com:5060;param1=value1;param2=value2"
    valid_uri_no_port = "sip:user@domain.com;param1=value1;param2=value2"
    valid_uri_bare_domain = "domain.com"

    def test_from_uri_valid(self):
        sip_uri = SIPURI.from_uri(self.valid_uri)
        assert sip_uri.user == "user"
        assert sip_uri.domain == "domain.com"
        assert sip_uri.port == 5060
        assert sip_uri.parameters == {"param1=value1", "param2=value2"}

    def test_from_uri_no_user(self):
        sip_uri = SIPURI.from_uri(self.valid_uri_no_user)
        assert sip_uri.user is None
        assert sip_uri.domain == "domain.com"
        assert sip_uri.port == 5060
        assert sip_uri.parameters == {"param1=value1", "param2=value2"}

    def test_from_uri_no_port(self):
        sip_uri = SIPURI.from_uri(self.valid_uri_no_port)
        assert sip_uri.user == "user"
        assert sip_uri.domain == "domain.com"
        assert sip_uri.port is None
        assert sip_uri.parameters == {"param1=value1", "param2=value2"}

    def test_from_uri_invalid(self):
        sip_uri = SIPURI.from_uri(self.valid_uri_bare_domain)
        assert sip_uri.user is None
        assert sip_uri.domain == "domain.com"
        assert sip_uri.port is None
        assert sip_uri.parameters == set()


class TestAddress:
    valid_address_with_display = '"John Doe" <sip:john@doe.com:5060>;param1=value1'
    valid_address_no_display = "<sip:john@doe.com:5060>;param1=value1"
    valid_address_no_params = '"John Doe" <sip:john@doe.com:5060>'
    invalid_address = "John Doe <john@doe.com>"

    # Test the `from_address` method
    def test_from_address_with_display_name(self):
        address = Address.from_address(self.valid_address_with_display)
        assert address.display_name == "John Doe"
        assert str(address.sip_uri) == "sip:john@doe.com:5060"
        assert address.parameters == {"param1=value1"}

    def test_from_address_no_display_name(self):
        address = Address.from_address(self.valid_address_no_display)
        assert address.display_name is None
        assert str(address.sip_uri) == "sip:john@doe.com:5060"
        assert address.parameters == {"param1=value1"}

    def test_from_address_no_params(self):
        address = Address.from_address(self.valid_address_no_params)
        assert address.display_name == "John Doe"
        assert str(address.sip_uri) == "sip:john@doe.com:5060"
        assert address.parameters == set()

    def test_from_address_invalid_format(self):
        with pytest.raises(ValueError):
            Address.from_address(self.invalid_address)

    # Test the `__str__` method
    def test_str_with_display_name_and_params(self):
        address = Address.from_address(self.valid_address_with_display)
        assert str(address) == self.valid_address_with_display

    def test_str_no_display_name(self):
        address = Address.from_address(self.valid_address_no_display)
        expected_str = "<sip:john@doe.com:5060>;param1=value1"
        assert str(address) == expected_str

    # Test `add_parameter` and `add_parameter_to_uri` methods
    def test_add_parameter(self):
        address = Address.from_address(self.valid_address_no_params)
        address.add_parameter("newparam=newvalue")
        assert "newparam=newvalue" in address.parameters
        assert str(address).endswith(";newparam=newvalue")

    def test_add_parameter_to_uri(self):
        address = Address.from_address(self.valid_address_no_params)
        address.add_parameter_to_uri("uriparam=urivalue")
        assert "uriparam=urivalue" in address.sip_uri.parameters


class TestSIP:
    class SubclassedSIP(SIP):
        def method(self) -> str:
            return "METHOD"

        def get_src_ip(self) -> str:
            return "127.0.0.1"

        def get_src_port(self) -> int:
            return 5060

    def test_method(self):
        # Pycharm's type inspection struggles with `attrs`
        # noinspection PyTypeChecker
        subclassed = self.SubclassedSIP(
            to_field='"Linus Mixson" <sip:linus@opensettlenet.com>',
            from_field='"Nigel Daniels" <sip:nigel@opensettlenet.com>',
            call_id="4e8c8a35-3c35-4e24-a227-528ca2294f79",
            cseq="1",
            max_forwards="70",
            contact="sip:admin@opensettlenet.com",
        )

        assert subclassed.method() == "METHOD"

    def test_format_headers(self):
        # noinspection PyTypeChecker
        subclassed = self.SubclassedSIP(
            to_field='"Linus Mixson" <sip:linus@opensettlenet.com>',
            from_field='"Nigel Daniels" <sip:nigel@opensettlenet.com>',
            call_id="4e8c8a35-3c35-4e24-a227-528ca2294f79",
            cseq="1",
            max_forwards="70",
            contact="sip:admin@opensettlenet.com",
        )
        assert subclassed.format_headers() == (
            "Via: SIP/2.0/UDP 127.0.0.1:5060\r\n"
            'To: "Linus Mixson" <sip:linus@opensettlenet.com>\r\n'
            'From: "Nigel Daniels" <sip:nigel@opensettlenet.com>\r\n'
            "CSeq: 1 METHOD\r\n"
            "Call-ID: 4e8c8a35-3c35-4e24-a227-528ca2294f79\r\n"
            "Contact: sip:admin@opensettlenet.com\r\n"
            "Max-Forwards: 70\r\n"
            "Content-Length: 0\r\n"
        )

    def test_format_with_body(self):
        # noinspection PyTypeChecker
        subclassed = self.SubclassedSIP(
            to_field='"Linus Mixson" <sip:linus@opensettlenet.com>',
            from_field='"Nigel Daniels" <sip:nigel@opensettlenet.com>',
            call_id="4e8c8a35-3c35-4e24-a227-528ca2294f79",
            cseq="1",
            max_forwards="70",
            contact="sip:admin@opensettlenet.com",
        )
        assert subclassed.format() == (
            "METHOD sip:linus@opensettlenet.com SIP/2.0\r\n"
            "Via: SIP/2.0/UDP 127.0.0.1:5060\r\n"
            'To: "Linus Mixson" <sip:linus@opensettlenet.com>\r\n'
            'From: "Nigel Daniels" <sip:nigel@opensettlenet.com>\r\n'
            "CSeq: 1 METHOD\r\n"
            "Call-ID: 4e8c8a35-3c35-4e24-a227-528ca2294f79\r\n"
            "Contact: sip:admin@opensettlenet.com\r\n"
            "Max-Forwards: 70\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )

    def test_format_without_body(self):
        # noinspection PyTypeChecker
        subclassed = self.SubclassedSIP(
            to_field='"Linus Mixson" <sip:linus@opensettlenet.com>',
            from_field='"Nigel Daniels" <sip:nigel@opensettlenet.com>',
            call_id="4e8c8a35-3c35-4e24-a227-528ca2294f79",
            cseq="1",
            max_forwards="70",
            contact="sip:admin@opensettlenet.com",
            body="SIP BODY",
        )
        assert subclassed.format() == (
            "METHOD sip:linus@opensettlenet.com SIP/2.0\r\n"
            "Via: SIP/2.0/UDP 127.0.0.1:5060\r\n"
            'To: "Linus Mixson" <sip:linus@opensettlenet.com>\r\n'
            'From: "Nigel Daniels" <sip:nigel@opensettlenet.com>\r\n'
            "CSeq: 1 METHOD\r\n"
            "Call-ID: 4e8c8a35-3c35-4e24-a227-528ca2294f79\r\n"
            "Contact: sip:admin@opensettlenet.com\r\n"
            "Max-Forwards: 70\r\n"
            "Content-Length: 8\r\n"
            "\r\n"
            "SIP BODY"
        )
