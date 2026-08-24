# -*- coding: utf-8 -*-
"""Auto-extract cookies from local browsers for all supported platforms.

Supports: Chrome, Firefox, Edge, Brave, Opera
Extracts: Twitter (auth_token + ct0) only — this fork's other channels are credential-free.

Usage:
    agent-reach configure --from-browser chrome
"""

from typing import Any, Dict, List, Tuple

# Platform cookie specs: (platform_name, domain_pattern, needed_cookies)
PLATFORM_SPECS: list[dict[str, Any]] = [
    {
        "name": "Twitter/X",
        "domains": [".x.com", ".twitter.com"],
        "cookies": ["auth_token", "ct0"],
        "config_key": "twitter",
    },
]


def _chrome_profile_cookie_file(profile: str) -> str:
    """Resolve a Chrome profile name (e.g. 'Profile 6', 'Default') to its Cookies DB.

    Chromium keeps a separate cookie store per profile. browser_cookie3 reads
    'Default' unless pointed at a specific file, so multi-profile users must
    name their profile explicitly. Raises FileNotFoundError with the available
    profiles listed when the requested one has no cookie store.
    """
    import os
    import sys

    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif sys.platform.startswith("win"):
        base = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    else:
        base = os.path.expanduser("~/.config/google-chrome")

    for candidate in (
        os.path.join(base, profile, "Cookies"),
        os.path.join(base, profile, "Network", "Cookies"),
    ):
        if os.path.exists(candidate):
            return candidate

    available = []
    try:
        for entry in sorted(os.listdir(base)):
            if os.path.exists(os.path.join(base, entry, "Cookies")) or os.path.exists(
                os.path.join(base, entry, "Network", "Cookies")
            ):
                available.append(entry)
    except OSError:
        pass
    raise FileNotFoundError(
        f"No Chrome cookie store for profile {profile!r}. "
        f"Profiles with cookies: {', '.join(available) or '(none found)'}"
    )


def extract_all(browser: str = "chrome", profile: str | None = None) -> Dict[str, dict]:
    """
    Extract cookies for all supported platforms from the specified browser.

    Returns:
        {
            "twitter": {"auth_token": "xxx", "ct0": "yyy"},
        }
    """
    # Try rookiepy first (Rust-based, more stable), fallback to browser_cookie3.
    # A named profile forces browser_cookie3: it accepts an explicit cookie_file,
    # which is how per-profile selection is implemented here.
    use_rookiepy = False
    try:
        if profile and browser == "chrome":
            raise ImportError  # route to browser_cookie3 for profile support
        import rookiepy

        use_rookiepy = True
    except ImportError:
        try:
            import browser_cookie3
        except ImportError:
            raise RuntimeError(
                "Cookie extraction requires rookiepy or browser_cookie3.\n"
                "Install: pip install rookiepy  (recommended)\n"
                "     or: pip install browser-cookie3"
            )

    browser = browser.lower()
    supported = ["chrome", "firefox", "edge", "brave", "opera"]
    if browser not in supported:
        raise ValueError(f"Unsupported browser: {browser}. Supported: {', '.join(supported)}")

    if use_rookiepy:
        # rookiepy returns list of dicts with name/value/domain/path keys
        try:
            browser_funcs = {
                "chrome": rookiepy.chrome,
                "firefox": rookiepy.firefox,
                "edge": rookiepy.edge,
                "brave": rookiepy.brave,
                "opera": rookiepy.opera,
            }
            raw_cookies = browser_funcs[browser]()

            # Wrap into objects with .name, .value, .domain for compatibility
            class _Cookie:
                def __init__(self, d):
                    self.name = d.get("name", "")
                    self.value = d.get("value", "")
                    self.domain = d.get("domain", "")

            cookie_jar = [_Cookie(c) for c in raw_cookies]
        except Exception as e:
            raise RuntimeError(
                f"Could not read {browser} cookies via rookiepy: {e}\n"
                f"Make sure {browser} is closed and you have permission."
            )
    else:
        browser_funcs = {
            "chrome": browser_cookie3.chrome,
            "firefox": browser_cookie3.firefox,
            "edge": browser_cookie3.edge,
            "brave": browser_cookie3.brave,
            "opera": browser_cookie3.opera,
        }
        kwargs = {}
        if profile and browser == "chrome":
            kwargs["cookie_file"] = _chrome_profile_cookie_file(profile)
        try:
            cookie_jar = browser_funcs[browser](**kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Could not read {browser} cookies: {e}\n"
                f"Make sure {browser} is closed and you have permission."
            )

    results: dict[str, dict[str, str]] = {}

    for spec in PLATFORM_SPECS:
        platform_cookies = {}
        all_cookies_for_domain = []

        for cookie in cookie_jar:
            # Check if cookie belongs to this platform
            domain_match = any(
                cookie.domain.endswith(d) or cookie.domain == d.lstrip(".") for d in spec["domains"]
            )
            if not domain_match:
                continue

            all_cookies_for_domain.append(cookie)

            if spec["cookies"] is not None:
                if cookie.name in spec["cookies"]:
                    platform_cookies[cookie.name] = cookie.value

        if spec["cookies"] is None:
            # Grab all as header string
            if all_cookies_for_domain:
                cookie_str = "; ".join(f"{c.name}={c.value}" for c in all_cookies_for_domain)
                results[spec["config_key"]] = {"cookie_string": cookie_str}
        else:
            if platform_cookies:
                results[spec["config_key"]] = platform_cookies

    return results


def configure_from_browser(
    browser: str, config, profile: str | None = None
) -> List[Tuple[str, bool, str]]:
    """
    Extract cookies and configure all found platforms.

    Returns list of (platform_name, success, message) tuples.
    """
    results_list = []

    try:
        extracted = extract_all(browser, profile=profile)
    except Exception as e:
        return [("Browser", False, str(e))]

    if not extracted:
        return [
            (
                "All platforms",
                False,
                f"No platform cookies found in {browser}. "
                f"Make sure you're logged into x.com in {browser}.",
            )
        ]

    # Configure each found platform
    if "twitter" in extracted:
        tc = extracted["twitter"]
        if "auth_token" in tc and "ct0" in tc:
            config.set("twitter_auth_token", tc["auth_token"])
            config.set("twitter_ct0", tc["ct0"])
            results_list.append(("Twitter/X", True, "auth_token + ct0"))
        else:
            found = ", ".join(tc.keys())
            missing = [k for k in ["auth_token", "ct0"] if k not in tc]
            results_list.append(
                (
                    "Twitter/X",
                    False,
                    f"Found {found}, but missing: {', '.join(missing)}. "
                    f"Make sure you're logged into x.com in {browser}.",
                )
            )

    return results_list
