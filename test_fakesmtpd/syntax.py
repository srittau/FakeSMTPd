from unittest import TestCase

from asserts import assert_false, assert_true, assert_raises, assert_equal

from fakesmtpd.syntax import is_valid_address_literal, parse_reverse_path, \
    parse_path


class AddressLiteralTest(TestCase):
    def test_missing_brackets(self) -> None:
        assert_false(is_valid_address_literal("192.168.23.24"))

    def test_invalid_literal(self) -> None:
        assert_false(is_valid_address_literal("[INVALID]"))

    def test_valid_ipv4(self) -> None:
        assert_true(is_valid_address_literal("[192.168.23.24]"))

    def test_ipv4_out_of_bounds(self) -> None:
        assert_false(is_valid_address_literal("[192.256.23.24]"))

    def test_valid_full_ipv6(self) -> None:
        assert_true(is_valid_address_literal("[IPv6:0:0:0:0:0:0:0:0]"))

    def test_valid_comp_ipv6(self) -> None:
        assert_true(is_valid_address_literal("[IPv6:0:0::0]"))

    def test_comp_ipv6__too_many_groups(self) -> None:
        assert_false(is_valid_address_literal("[IPv6:0:0:0:0:0:0::0]"))

    def test_valid_full_ipv6v4(self) -> None:
        assert_true(
            is_valid_address_literal("[IPv6:0:0:0:0:0:0:192.168.9.12]"))

    def test_full_ipv6v4__invalid_ip4(self) -> None:
        assert_false(
            is_valid_address_literal("[IPv6:0:0:0:0:0:0:192.567.9.12]"))

    def test_valid_comp_ipv6v4(self) -> None:
        assert_true(is_valid_address_literal("[IPv6:0:0::0:192.168.9.12]"))

    def test_comp_ipv6v4__too_many_groups(self) -> None:
        assert_false(
            is_valid_address_literal("[IPv6:0:0:0:0::0:192.168.9.12]"))

    def test_comp_ipv6v4__ends_with_empty_group(self) -> None:
        assert_true(is_valid_address_literal("[IPv6:0:0:0:0::192.168.9.12]"))

    def test_comp_ipv6v4__invalid_ip4(self) -> None:
        assert_false(is_valid_address_literal("[IPv6:0:0::0:192.168.9.333]"))


class PathTest(TestCase):
    def test_mailbox(self) -> None:
        path, rest = parse_reverse_path("<foo@example.com>")
        assert_equal("foo@example.com", path)
        assert_equal("", rest)

    def test_mailbox_with_rest(self) -> None:
        path, rest = parse_reverse_path("<foo@example.com>REST")
        assert_equal("foo@example.com", path)
        assert_equal("REST", rest)

    def test_quoted_string(self) -> None:
        path, rest = parse_reverse_path('<"foo \\" bar"@example.com>')
        assert_equal('"foo \\" bar"@example.com', path)
        assert_equal("", rest)

    def test_empty_path(self) -> None:
        with assert_raises(ValueError):
            parse_path("<>")

    def test_invalid(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("INVALID")

    def test_missing_at(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("<invalid>")

    def test_invalid_no_local_part(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("<@example.com>")

    def test_invalid_local_part(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("<@@example.com>")

    def test_no_domain(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("<foo@>")

    def test_invalid_domain(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("<foo@*>")


class ReversePathTest(TestCase):
    def test_empty_path(self) -> None:
        path, rest = parse_reverse_path("<>")
        assert_equal("", path)
        assert_equal("", rest)

    def test_empty_path_with_rest(self) -> None:
        path, rest = parse_reverse_path("<>REST")
        assert_equal("", path)
        assert_equal("REST", rest)

    def test_mailbox(self) -> None:
        path, rest = parse_reverse_path("<foo@example.com>REST")
        assert_equal("foo@example.com", path)
        assert_equal("REST", rest)

    def test_invalid(self) -> None:
        with assert_raises(ValueError):
            parse_reverse_path("INVALID")
