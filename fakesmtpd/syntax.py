import re
from typing import List, Optional, Tuple

from fakesmtpd.smtp import (
    PATH_TOO_LONG_MSG,
    SMTP_DOMAIN_LIMIT,
    SMTP_LOCAL_PART_LIMIT,
    SMTP_PATH_LIMIT,
    SYNTAX_ERROR_MSG,
)

_LET_DIG = r"[a-zA-Z0-9]"
_LDH_STR = f"[a-zA-Z0-9-]*{_LET_DIG}"
_SNUM = r"[0-9]{1,3}"
_IPV6_HEX = r"[0-9a-fA-F]{1,4}"
_ATOM = r"[0-9a-zA-Z!#$%&'*+/=?^_`{}|~-]+"
_DOT_STRING = f"{_ATOM}(\\.{_ATOM})*"
_Q_TEXT_SMTP = r"[ !#-\[\]-~]"
_QP_SMTP = r"\\[ -~]"
_QUOTED_STRING = f'"(({_Q_TEXT_SMTP})|({_QP_SMTP}))*"'

_SUB_DOMAIN = f"{_LET_DIG}({_LDH_STR})?"
_DOMAIN = f"{_SUB_DOMAIN}(\\.{_SUB_DOMAIN})*"

_IPV4_LITERAL = f"({_SNUM})\\.({_SNUM})\\.({_SNUM})\\.({_SNUM})"
_ADDRESS_LITERAL = r"\[(.*)\]"

_IPV6_FULL = f"{_IPV6_HEX}(:{_IPV6_HEX}){{7}}"
_IPV6_COMP = f"({_IPV6_HEX}(:{_IPV6_HEX})*)?::({_IPV6_HEX}(:{_IPV6_HEX})*)?"
_IPV6V4_FULL = f"{_IPV6_HEX}(:{_IPV6_HEX}){{5}}:({_IPV4_LITERAL})"
_IPV6V4_COMP = (
    f"(({_IPV6_HEX}(:{_IPV6_HEX})*)?::({_IPV6_HEX}(:{_IPV6_HEX})*:)?)"
    f"({_IPV4_LITERAL})"
)

_ESMTP_PARAM = "([a-zA-Z0-9][a-zA-Z0-9-]*)(=([!-<>-~]+))?"

_dot_string_re = re.compile(f"^{_DOT_STRING}$")
_quoted_string_re = re.compile(f"^{_QUOTED_STRING}$")

_domain_re = re.compile(f"^{_DOMAIN}$")
_ipv4_re = re.compile(f"^{_IPV4_LITERAL}$")
_ipv6_full_re = re.compile(f"^{_IPV6_FULL}$")
_ipv6_comp_re = re.compile(f"^{_IPV6_COMP}$")
_ipv6v4_full_re = re.compile(f"^{_IPV6V4_FULL}$")
_ipv6v4_comp_re = re.compile(f"^{_IPV6V4_COMP}$")
_address_literal_re = re.compile(f"^{_ADDRESS_LITERAL}$")

_esmtp_param_re = re.compile(f"^{_ESMTP_PARAM}$")


def is_valid_domain(s: str) -> bool:
    return _domain_re.match(s) is not None


def is_valid_address_literal(s: str) -> bool:
    # General-address-literals are not supported.
    m = _address_literal_re.match(s)
    if m is None:
        return False
    lit = m.group(1)
    if is_valid_ipv4_address(lit):
        return True
    elif lit.startswith("IPv6:") and is_valid_ipv6_address(lit[5:]):
        return True
    else:
        return False


def is_valid_ipv4_address(s: str) -> bool:
    m = _ipv4_re.match(s)
    if m is None:
        return False
    digits = [int(m.group(i)) for i in range(1, 5)]
    return all(0 <= d <= 255 for d in digits)


def is_valid_ipv6_address(s: str) -> bool:
    if _ipv6_full_re.match(s) is not None:
        return True
    elif _ipv6_comp_re.match(s) is not None:
        g1, g2 = s.split("::")
        group_count = g1.count(":") + g2.count(":") + 2
        return group_count <= 6
    m1 = _ipv6v4_full_re.match(s)
    if m1 is not None:
        ipv4 = m1.group(2)
        return is_valid_ipv4_address(ipv4)
    m2 = _ipv6v4_comp_re.match(s)
    if m2 is not None:
        ipv6 = m2.group(1)
        g1, g2 = ipv6.split("::")
        assert g2 == "" or g2.endswith(":")
        group_count = g1.count(":") + g2.count(":") + 1
        ipv4 = m2.group(6)
        return group_count <= 4 and is_valid_ipv4_address(ipv4)
    return False


def parse_path(s: str) -> Tuple[str, str]:
    m = re.match(r"^<(.*)>", s)
    if not m:
        raise ValueError(SYNTAX_ERROR_MSG)
    path = m.group(1)
    if len(path) + 2 > SMTP_PATH_LIMIT:
        raise ValueError(PATH_TOO_LONG_MSG)
    _validate_mailbox(path)
    return path, s[len(path) + 2 :]


def _validate_mailbox(s: str) -> None:
    try:
        local_part, domain = s.split("@")
    except ValueError:
        raise ValueError(SYNTAX_ERROR_MSG)
    _validate_local_part(local_part)
    _validate_domain_part(domain)


def _validate_local_part(s: str) -> None:
    if len(s) > SMTP_LOCAL_PART_LIMIT:
        raise ValueError(PATH_TOO_LONG_MSG)
    if not (_is_valid_dot_string(s) or _is_valid_quoted_string(s)):
        raise ValueError(SYNTAX_ERROR_MSG)


def _is_valid_dot_string(s: str) -> bool:
    return _dot_string_re.match(s) is not None


def _is_valid_quoted_string(s: str) -> bool:
    return _quoted_string_re.match(s) is not None


def _validate_domain_part(s: str) -> None:
    if len(s) > SMTP_DOMAIN_LIMIT:
        raise ValueError(PATH_TOO_LONG_MSG)
    if not (is_valid_domain(s) or is_valid_address_literal(s)):
        raise ValueError(SYNTAX_ERROR_MSG)


def parse_reverse_path(s: str) -> Tuple[str, str]:
    if s.startswith("<>"):
        return "", s[2:]
    return parse_path(s)


parse_forward_path = parse_path


def parse_receiver(s: str) -> Tuple[str, str]:
    if s[:12].lower() == "<postmaster>":
        return s[1:11], s[12:]
    return parse_forward_path(s)


def is_valid_smtp_arguments(s: str) -> bool:
    if s.startswith(" "):
        try:
            parse_smtp_arguments(s[1:])
        except ValueError:
            return False
    elif s:
        return False
    return True


def parse_smtp_arguments(s: str) -> List[Tuple[str, Optional[str]]]:
    return [_parse_estm_param(sub) for sub in s.split(" ")]


def _parse_estm_param(s: str) -> Tuple[str, Optional[str]]:
    m = _esmtp_param_re.match(s)
    if not m:
        raise ValueError(SYNTAX_ERROR_MSG)
    return m.group(1), m.group(3)
