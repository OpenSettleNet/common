import pytest
from pydantic import BaseConfig

from opensettlenet_common.sip import Notify, Publish, Subscribe, SIPURI, Address


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


def test_injection():
    config = object()
    injected_notify = Notify.inject_config(config)  # type: ignore
    assert injected_notify.get_config() == config
    injected_publish = Publish.inject_config(config)  # type: ignore
    assert injected_publish.get_config() == config
    injected_subscribe = Subscribe.inject_config(config)  # type: ignore
    assert injected_subscribe.get_config() == config
