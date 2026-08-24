# -*- coding: utf-8 -*-
"""
Agent Reach CLI — installer, doctor, and configuration tool.

Usage:
    agent-reach install --env=auto
    agent-reach doctor
    agent-reach configure twitter-cookies
    agent-reach setup
"""

import argparse
import getpass
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from agent_reach import __version__

# Pinned to the 0.4.2 state — PyPI still only has 0.4.1 (upstream issue #10).
_RDT_GIT_SOURCE = (
    "git+https://github.com/public-clis/rdt-cli.git@5e4fb3720d5c174e976cd425ccc3b879d52cac66"
)


def _ensure_utf8_console():
    """Best-effort Windows console UTF-8 setup for CLI runtime only."""
    if sys.platform != "win32":
        return
    # Avoid interfering with pytest/captured streams.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    try:
        import io

        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        # Do not crash CLI just because encoding patch failed.
        pass


def _configure_logging(verbose: bool = False):
    """Suppress loguru output unless --verbose is set."""
    from loguru import logger

    logger.remove()  # Remove default stderr handler
    if verbose:
        logger.add(sys.stderr, level="INFO")


def main():
    _ensure_utf8_console()

    parser = argparse.ArgumentParser(
        prog="agent-reach",
        description="Give your AI Agent eyes to see the entire internet",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug logs")
    parser.add_argument("--version", action="version", version=f"Agent Reach v{__version__}")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── setup ──
    sub.add_parser("setup", help="Interactive configuration wizard")

    # ── install ──
    p_install = sub.add_parser("install", help="One-shot installer with flags")
    p_install.add_argument(
        "--env",
        choices=["local", "server", "auto"],
        default="auto",
        help="Environment: local, server, or auto-detect",
    )
    p_install.add_argument(
        "--safe",
        action="store_true",
        help="Safe mode: skip automatic system changes, show what's needed instead",
    )
    p_install.add_argument(
        "--yes",
        action="store_true",
        help="Explicitly consent to user-level installs and configuration writes",
    )
    p_install.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making any changes"
    )
    p_install.add_argument(
        "--channels",
        default="",
        help="Comma-separated optional channels to install "
        "(twitter,xiaoyuzhou,xueqiu,xiaohongshu,"
        "reddit,bilibili,linkedin,all)",
    )

    # ── configure ──
    p_conf = sub.add_parser("configure", help="Set a config value or auto-extract from browser")
    p_conf.add_argument(
        "key",
        nargs="?",
        default=None,
        choices=[
            "github-token",
            "groq-key",
            "openai-key",
            "twitter-cookies",
            "youtube-cookies",
            "xhs-cookies",
        ],
        help="What to configure (omit if using --from-browser)",
    )
    p_conf.add_argument(
        "value",
        nargs="*",
        help="Deprecated for secrets; use --stdin, --file, or an interactive prompt",
    )
    p_conf_source = p_conf.add_mutually_exclusive_group()
    p_conf_source.add_argument(
        "--stdin",
        action="store_true",
        help="Read the value from standard input (recommended for automation)",
    )
    p_conf_source.add_argument(
        "--file",
        type=Path,
        help="Read the value from a local file",
    )
    p_conf.add_argument(
        "--from-browser",
        metavar="BROWSER",
        choices=["chrome", "firefox", "edge", "brave", "opera"],
        help="Auto-extract ALL platform cookies from browser (chrome/firefox/edge/brave/opera)",
    )

    # ── doctor ──
    p_doctor = sub.add_parser("doctor", help="Check platform availability")
    p_doctor.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of the text report",
    )

    # ── uninstall ──
    p_uninstall = sub.add_parser(
        "uninstall", help="Remove all Agent Reach config, tokens, and skill files"
    )
    p_uninstall.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making any changes",
    )
    p_uninstall.add_argument(
        "--keep-config",
        action="store_true",
        help="Remove skill files only, keep ~/.agent-reach/ config and tokens",
    )

    # ── skill ──
    p_skill = sub.add_parser("skill", help="Manage agent skill registration")
    p_skill_group = p_skill.add_mutually_exclusive_group(required=True)
    p_skill_group.add_argument(
        "--install", action="store_true", help="Install SKILL.md to agent skill directories"
    )
    p_skill_group.add_argument(
        "--uninstall", action="store_true", help="Remove SKILL.md from agent skill directories"
    )
    p_skill.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing customized skill installation",
    )

    # ── format ──
    p_format = sub.add_parser("format", help="Clean and format platform API output")
    p_format.add_argument("platform", choices=["xhs"], help="Platform to format (xhs)")

    # ── check-update ──
    # ── transcribe ──
    p_tr = sub.add_parser(
        "transcribe", help="Transcribe a URL or local audio file (Whisper via Groq/OpenAI)"
    )
    p_tr.add_argument("source", help="Audio/video URL or local file path")
    p_tr.add_argument(
        "--provider",
        choices=["auto", "groq", "openai"],
        default="auto",
        help="Transcription provider (default: auto = groq → openai fallback)",
    )
    p_tr.add_argument(
        "-o", "--output", default=None, help="Write transcript to a file instead of stdout"
    )

    sub.add_parser("check-update", help="Check for new versions and changes")

    # ── watch ──
    p_watch = sub.add_parser(
        "watch",
        help="Check a recorded channel baseline and package update status",
    )
    p_watch.add_argument(
        "--channels",
        default="",
        help="Comma-separated channels to monitor (default: recorded baseline)",
    )
    p_watch.add_argument(
        "--record-baseline",
        action="store_true",
        help="Explicitly save current selected-channel health as the new baseline",
    )

    # ── version ──
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "version":
        print(f"Agent Reach v{__version__}")
        sys.exit(0)

    # Suppress loguru noise only after dependency-free help/version handling.
    _configure_logging(getattr(args, "verbose", False))

    result = None
    if args.command == "doctor":
        result = _cmd_doctor(args)
    elif args.command == "check-update":
        result = _cmd_check_update()
    elif args.command == "watch":
        result = _cmd_watch(args)
    elif args.command == "setup":
        result = _cmd_setup()
    elif args.command == "install":
        result = _cmd_install(args)
    elif args.command == "configure":
        result = _cmd_configure(args)
    elif args.command == "uninstall":
        result = _cmd_uninstall(args)
    elif args.command == "skill":
        result = _cmd_skill(args)
    elif args.command == "format":
        result = _cmd_format(args)
    elif args.command == "transcribe":
        result = _cmd_transcribe(args)
    if result == "error":
        raise SystemExit(2)
    if isinstance(result, int) and result:
        raise SystemExit(result)


# ── Command handlers ────────────────────────────────


def _cmd_install(args):
    """One-shot deterministic installer."""
    import os

    from agent_reach.config import Config
    from agent_reach.doctor import check_all, format_report

    approved = bool(getattr(args, "yes", False))
    safe_mode = args.safe or not approved
    dry_run = args.dry_run

    config = Config(create=approved and not dry_run and not safe_mode)
    print()
    print("Agent Reach Installer")
    print("=" * 40)

    # Ensure tools directory exists (for upstream tool repos)
    tools_dir = os.path.expanduser("~/.agent-reach/tools")
    if approved and not dry_run and not safe_mode:
        os.makedirs(tools_dir, mode=0o700, exist_ok=True)

    if dry_run:
        print("DRY RUN — showing what would be done (no changes)")
        print()
    if safe_mode:
        if not approved:
            print("PLAN MODE — no changes without explicit --yes consent")
        else:
            print("SAFE MODE — skipping automatic system changes")
        print()

    # ── Parse --channels ──
    CHANNEL_INSTALLERS = {
        "twitter": _install_twitter_deps,
        "xiaoyuzhou": _install_xiaoyuzhou_deps,
        "xiaohongshu": _install_xhs_deps,
        "reddit": _install_reddit_deps,
        "bilibili": _install_bili_deps,
        "opencli": _install_opencli_deps,  # cross-channel backend, desktop only
        # xueqiu: cookie-only, no install step
        # linkedin: manual setup, no auto-install
    }
    COOKIE_CHANNELS = {"twitter", "xueqiu", "bilibili"}

    requested_channels = set()
    if args.channels:
        raw = [c.strip().lower() for c in args.channels.split(",") if c.strip()]
        if "all" in raw:
            requested_channels = set(CHANNEL_INSTALLERS.keys()) | {"xueqiu", "linkedin"}
        else:
            requested_channels = set(raw)

    # Auto-detect environment
    env = args.env
    if env == "auto":
        env = _detect_environment()

    if env == "server":
        print("Environment: Server/VPS (auto-detected)")
    else:
        print("Environment: Local computer (auto-detected)")

    # ── Install core system dependencies (lightweight, always) ──
    print()
    if dry_run:
        _install_system_deps_dryrun()
    elif safe_mode:
        _install_system_deps_safe()
    else:
        _install_system_deps()

    # ── mcporter (for Exa search) ──
    print()
    if dry_run:
        print("[dry-run] Would check mcporter and configure Exa only if already installed")
    elif safe_mode:
        _install_mcporter_safe()
    else:
        _install_mcporter()

    # ── Install optional channels (only if --channels specified) ──
    if requested_channels and not dry_run and not safe_mode:
        print()
        print("Installing optional channels...")
        if env == "server" and "opencli" in requested_channels:
            # OpenCLI rides a real desktop Chrome session — useless headless
            requested_channels.discard("opencli")
            print("  -- OpenCLI 需要桌面环境 + Chrome，服务器环境跳过")
        for ch_name in sorted(requested_channels):
            installer = CHANNEL_INSTALLERS.get(ch_name)
            if installer:
                installer()

    if requested_channels and dry_run:
        print()
        print(f"[dry-run] Would install optional channels: {', '.join(sorted(requested_channels))}")

    # ── Auto-import cookies (only if cookie-needing channels are requested) ──
    needs_cookies = bool(requested_channels & COOKIE_CHANNELS)
    if env == "local" and needs_cookies and not safe_mode and not dry_run:
        print()
        print("Importing cookies from browser...")
        print("  (macOS may ask for your login password to access the Keychain — this is normal,")
        print("   it only happens once during install. Enter your password or click 'Allow'.)")
        try:
            from agent_reach.cookie_extract import configure_from_browser

            cookie_results = configure_from_browser("chrome", config)
            found = False
            for platform, success, message in cookie_results:
                if success:
                    print(f"  ✅ {platform}: {message}")
                    found = True
            if not found:
                cookie_results = configure_from_browser("firefox", config)
                for platform, success, message in cookie_results:
                    if success:
                        print(f"  ✅ {platform}: {message}")
                        found = True
            if not found:
                print("  -- No cookies found (normal if you haven't logged into these sites)")
        except Exception:
            print(
                "  -- Could not read browser cookies (browser might be open or password was denied)"
            )
    elif env == "local" and needs_cookies and dry_run:
        print()
        print("[dry-run] Would try to import cookies from Chrome/Firefox")

    # Environment-specific advice
    if env == "server":
        print()
        print("Tip: 部分平台对服务器 IP 有风控。")
        print("   Reddit 必须登录态（rdt-cli + Cookie，见 doctor 提示），中国大陆网络还需代理。")
        print("   如需代理，请通过系统凭据管理器注入 HTTP_PROXY/HTTPS_PROXY 环境变量。")
        print("   Cheap option: https://www.webshare.io ($1/month)")

    # Test channels
    if not dry_run:
        print()
        print("Testing channels...")
        health_results = check_all(config)
        ok = sum(1 for result in health_results.values() if result["status"] == "ok")
        total = len(health_results)

        # Final status
        print()
        print(format_report(health_results))
        print()

        if approved and not safe_mode:
            # Skill installation is part of the explicitly approved install,
            # but customized copies are still preserved unless force is used
            # through the dedicated skill command.
            _install_skill()
            print(f"✅ Installation complete! {ok}/{total} channels active.")
        else:
            print(f"Plan complete. {ok}/{total} channels are currently active; no changes made.")

        if not requested_channels:
            # First install — hint about optional channels
            print()
            print("More channels available! Use --channels to install:")
            print("   agent-reach install --channels=twitter,xiaohongshu,reddit,...")
            print("   agent-reach install --channels=all  (install everything)")

        # Star reminder
        print()
        print("如果 Agent Reach 帮到了你，给个 Star 让更多人发现它吧：")
        print("   https://github.com/Panniantong/Agent-Reach")
        print("   只需一秒，对独立开发者意义很大。谢谢！")
    else:
        print()
        print("Dry run complete. No changes were made.")


def _install_skill(*, force: bool = False):
    """Install Agent Reach as an agent skill (OpenClaw / Claude Code / .agents)."""
    import importlib.resources
    import os
    import shutil

    def _is_english_locale(value: str) -> bool:
        normalized = value.strip().lower()
        return normalized.startswith("en") or normalized.startswith("english")

    def _skill_resource_name() -> str:
        locale_candidates = (
            os.environ.get("AGENT_REACH_LANG", ""),
            os.environ.get("LC_ALL", ""),
            os.environ.get("LC_MESSAGES", ""),
            os.environ.get("LANG", ""),
        )
        if any(_is_english_locale(candidate) for candidate in locale_candidates):
            return "SKILL_en.md"
        return "SKILL.md"

    def _read_skill_markdown(skill_pkg):
        resource_name = _skill_resource_name()
        try:
            return skill_pkg.joinpath(resource_name).read_text(encoding="utf-8")
        except FileNotFoundError:
            return skill_pkg.joinpath("SKILL.md").read_text(encoding="utf-8")

    def _copy_skill_dir(target: str) -> bool:
        """Copy entire skill directory (locale-specific SKILL.md + references/)."""
        try:
            # Get skill directory from package (with fallback for editable installs)
            try:
                skill_pkg = importlib.resources.files("agent_reach").joinpath("skill")
                skill_md = _read_skill_markdown(skill_pkg)
            except Exception:
                from pathlib import Path

                skill_pkg = Path(__file__).resolve().parent / "skill"
                skill_md = _read_skill_markdown(skill_pkg)

            existing_skill = os.path.join(target, "SKILL.md")
            if os.path.lexists(target) and not force:
                if os.path.isfile(existing_skill):
                    with open(existing_skill, encoding="utf-8") as handle:
                        if handle.read() == skill_md:
                            return True
                print(f"  Preserved customized skill: {target}")
                print("  Re-run `agent-reach skill --install --force` to replace it.")
                return False

            # Replacement is allowed only after explicit --force or for a new target.
            if os.path.islink(target):
                os.unlink(target)
            elif os.path.exists(target):
                shutil.rmtree(target)
            os.makedirs(target, exist_ok=True)

            # Copy SKILL.md using the selected locale file
            with open(os.path.join(target, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_md)

            # Copy references/ directory
            refs_pkg = skill_pkg.joinpath("references")
            refs_target = os.path.join(target, "references")
            os.makedirs(refs_target, exist_ok=True)

            for ref_file in refs_pkg.iterdir():
                name = ref_file.name if hasattr(ref_file, "name") else str(ref_file).split("/")[-1]
                if name.endswith(".md"):
                    content = (
                        ref_file.read_text(encoding="utf-8")
                        if hasattr(ref_file, "read_text")
                        else ref_file.read_text()
                    )
                    with open(os.path.join(refs_target, name), "w", encoding="utf-8") as f:
                        f.write(content)

            return True
        except Exception as e:
            print(f"  Warning: Could not install skill: {e}")
            return False

    # Determine skill install path (priority: .agents > openclaw > claude)
    skill_dirs = [
        os.path.expanduser("~/.agents/skills"),  # Generic agents (priority)
        os.path.expanduser("~/.openclaw/skills"),  # OpenClaw
        os.path.expanduser("~/.claude/skills"),  # Claude Code (if exists)
    ]

    # Insert OPENCLAW_HOME path at the beginning if environment variable is set
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        skill_dirs.insert(0, os.path.join(openclaw_home, ".openclaw", "skills"))

    installed = False
    for skill_dir in skill_dirs:
        if os.path.isdir(skill_dir):
            target = os.path.join(skill_dir, "agent-reach")
            target_already_exists = os.path.lexists(target)
            if _copy_skill_dir(target):
                platform_name = (
                    "Agent"
                    if ".agents" in skill_dir
                    else "OpenClaw"
                    if "openclaw" in skill_dir
                    else "Claude Code"
                )
                print(f"Skill installed for {platform_name}: {target}")
                installed = True
            elif target_already_exists:
                # A preserved customization is an intentional terminal state;
                # do not create a second installation elsewhere.
                installed = True

    if not installed:
        # No known skill directory found — create for .agents by default
        target = os.path.expanduser("~/.agents/skills/agent-reach")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if _copy_skill_dir(target):
            print(f"Skill installed: {target}")
        else:
            print("  -- Could not install agent skill (optional)")
            print("  -- Tip: install OpenClaw, Claude Code, or create ~/.agents/skills/ manually")


def _uninstall_skill():
    """Remove SKILL.md from all known agent skill directories."""
    import shutil

    skill_dirs = [
        ("~/.openclaw/skills/agent-reach", "OpenClaw"),
        ("~/.claude/skills/agent-reach", "Claude Code"),
        ("~/.agents/skills/agent-reach", "Agent"),
    ]

    # Also check OPENCLAW_HOME
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        skill_dirs.insert(
            0,
            (os.path.join(openclaw_home, ".openclaw", "skills", "agent-reach"), "OpenClaw"),
        )

    removed = False
    for skill_path_template, platform_name in skill_dirs:
        skill_path = os.path.expanduser(skill_path_template)
        if os.path.isdir(skill_path):
            try:
                if os.path.islink(skill_path):
                    os.unlink(skill_path)
                else:
                    shutil.rmtree(skill_path)
                print(f"  Removed {platform_name} skill: {skill_path}")
                removed = True
            except Exception as e:
                print(f"  Could not remove {skill_path}: {e}")

    if not removed:
        print("  No skill installations found.")


def _cmd_skill(args):
    """Manage agent skill registration."""
    if args.install:
        _install_skill(force=args.force)
    elif args.uninstall:
        _uninstall_skill()


def _cmd_format(args):
    """Clean and format platform API output from stdin."""
    import json
    import sys

    if args.platform == "xhs":
        from agent_reach.channels.xiaohongshu import format_xhs_result

        raw = sys.stdin.read().strip()
        if not raw:
            print("Error: no input on stdin", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

        cleaned = format_xhs_result(data)
        print(json.dumps(cleaned, ensure_ascii=False, indent=2))


def _install_system_deps():
    """Inspect system dependencies without crossing privilege boundaries.

    Even after ``--yes`` Agent Reach does not write package-manager sources,
    run elevation, or execute downloaded setup scripts. Those operations need
    a separate, platform-native user decision.
    """

    import platform
    import shutil

    from agent_reach.utils.paths import set_ytdlp_option

    print("Checking system dependencies...")
    os_type = platform.system().lower()

    if shutil.which("gh"):
        print("  ✅ gh CLI already installed")
    else:
        if os_type == "darwin":
            print("  -- gh CLI missing. Review and run: brew install gh")
        elif os_type == "windows":
            print("  -- gh CLI missing. Review and run: winget install GitHub.cli")
        else:
            print("  -- gh CLI missing. Install from your OS repository or https://cli.github.com")

    if shutil.which("node") and shutil.which("npm"):
        print("  ✅ Node.js already installed")
    else:
        print("  -- Node.js/npm missing. Install a supported LTS release from https://nodejs.org")

    # ── yt-dlp JS runtime config (YouTube requires external JS runtime) ──
    if shutil.which("node"):
        try:
            path = set_ytdlp_option("--js-runtimes", "--js-runtimes node")
            print(f"  ✅ yt-dlp Node.js runtime configured in {path}")
        except OSError as exc:
            print(f"  -- Could not configure yt-dlp JS runtime: {exc}")

    # NOTE: twitter-cli, xiaoyuzhou, xhs-cli etc. are optional.
    # They are installed via --channels flag, not here.
    # See CHANNEL_INSTALLERS in _cmd_install().


def _install_xiaoyuzhou_deps():
    """Install Xiaoyuzhou podcast transcription script."""
    import shutil

    from agent_reach.config import Config

    config = Config()
    print("Setting up Xiaoyuzhou podcast transcription...")

    tools_dir = os.path.expanduser("~/.agent-reach/tools/xiaoyuzhou")
    script_dst = os.path.join(tools_dir, "transcribe.sh")

    if os.path.isfile(script_dst):
        print("  ✅ Xiaoyuzhou transcription script already installed")
    else:
        # Copy script from package
        script_src = os.path.join(os.path.dirname(__file__), "scripts", "transcribe_xiaoyuzhou.sh")
        if os.path.isfile(script_src):
            try:
                os.makedirs(tools_dir, exist_ok=True)
                import shutil as _shutil

                _shutil.copy2(script_src, script_dst)
                os.chmod(script_dst, 0o755)
                print("  ✅ Xiaoyuzhou transcription script installed")
            except Exception as e:
                print(f"  [!]  Failed to install script: {e}")
        else:
            print("  [!]  Script source not found in package")

    # Check ffmpeg
    if shutil.which("ffmpeg"):
        print("  ✅ ffmpeg available")
    else:
        print("  -- ffmpeg not found. Install: apt install -y ffmpeg (or brew install ffmpeg)")

    # Check GROQ_API_KEY
    has_key = bool(os.environ.get("GROQ_API_KEY")) or bool(config.get("groq_api_key"))
    if has_key:
        print("  ✅ Groq API key configured")
    else:
        print("  -- Groq API key not set. Get a key at https://console.groq.com")
        print("     Then run the hidden prompt: agent-reach configure groq-key")


def _install_twitter_deps():
    """Report the reviewed-version requirement for twitter-cli."""
    import shutil

    print("Setting up Twitter (twitter-cli)...")
    if shutil.which("twitter"):
        print("  ✅ twitter-cli already installed")
        return
    print("  -- Not auto-installing an unpinned external package.")
    print("     Review an exact twitter-cli release, then install twitter-cli==VERSION.")


def _install_xhs_deps():
    """Set up XiaoHongShu — backend depends on environment.

    Desktop: OpenCLI (reuses the browser session, zero config).
    Server: xiaohongshu-mcp guide (self-contained headless browser + QR
    login; we don't manage long-running services, so guide only).
    xhs-cli is no longer installed by default — upstream unmaintained
    since 2026-03; existing installs keep working as a fallback backend.
    """
    import shutil

    print("Setting up XiaoHongShu...")
    if _detect_environment() == "server":
        print("  服务器环境推荐 xiaohongshu-mcp（自带无头浏览器，扫码登录）：")
        print("    1. 下载 binary：https://github.com/xpzouying/xiaohongshu-mcp/releases")
        print("       （建议放到 ~/.agent-reach/tools/ 下）")
        print("    2. 启动服务（首次运行会下载约 150MB 浏览器，请等待完成）")
        print("    3. 扫码登录后接入：mcporter config add xiaohongshu http://localhost:18060/mcp")
        print("    4. 验证：agent-reach doctor")
        return

    _install_opencli_deps()
    if shutil.which("xhs"):
        print("  ✅ 检测到存量 xhs-cli，将作为备选后端继续可用")


def _install_opencli_deps():
    """Diagnose OpenCLI — cross-platform backend riding the user's Chrome session.

    Desktop-only. Agent Reach does not float a global npm package or install
    the Chrome extension programmatically.
    """
    from agent_reach.backends import (
        OPENCLI_EXTENSION_URL,
        OPENCLI_PACKAGE,
        opencli_status,
        opencli_summary,
    )

    print("Setting up OpenCLI (browser-session backend, desktop only)...")
    st = opencli_status()
    if st.installed and not st.broken:
        print(f"  ✅ {opencli_summary(st)}")
        if not st.ready:
            print(f"  {st.hint}")
        return

    print("  -- Not auto-installing a floating global npm package.")
    print(f"     Review an exact {OPENCLI_PACKAGE} release, then install PACKAGE@VERSION.")
    print(f"     Chrome extension (manual user action): {OPENCLI_EXTENSION_URL}")


def _install_reddit_deps():
    """Set up Reddit — desktop prefers OpenCLI, rdt-cli for servers/legacy.

    No zero-config path exists (anonymous .json blocked, official API
    approval-gated since 2025-11) — every backend needs a logged-in session.
    """
    if _detect_environment() != "server":
        _install_opencli_deps()
        print("  Reddit 走 OpenCLI（浏览器里登录过 reddit.com 即可用）")
        import shutil

        if shutil.which("rdt"):
            print("  ✅ 检测到存量 rdt-cli，将作为备选后端继续可用")
        return

    _install_rdt_cli()


def _install_rdt_cli():
    """Install rdt-cli (pinned git source — PyPI lags upstream)."""
    import shutil
    import subprocess

    print("Setting up Reddit (rdt-cli)...")
    if shutil.which("rdt"):
        print("  ✅ rdt-cli already installed")
        return
    for tool, cmd in [
        ("pipx", ["pipx", "install", _RDT_GIT_SOURCE]),
        ("uv", ["uv", "tool", "install", "--from", _RDT_GIT_SOURCE, "rdt-cli"]),
    ]:
        if shutil.which(tool):
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=120
                )
                if proc.returncode != 0:
                    tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:]
                    print(
                        f"  [!]  {tool} exited {proc.returncode}" + (f": {tail[0]}" if tail else "")
                    )
                    continue
                if shutil.which("rdt"):
                    print("  ✅ rdt-cli installed")
                    return
                print(f"  [!]  {tool} reported success but 'rdt' is not on PATH")
            except Exception as e:
                print(f"  [!]  {tool} install attempt failed: {e}")
    print(f"  [!]  rdt-cli install failed. Run: pipx install '{_RDT_GIT_SOURCE}'")


def _install_bili_deps():
    """Report the reviewed-version requirement for bili-cli."""
    import shutil

    print("Setting up Bilibili (bili-cli)...")
    if shutil.which("bili"):
        print("  ✅ bili-cli already installed")
        return
    print("  -- bili-cli is unmaintained and is not auto-installed.")
    print("     Review and pin an exact upstream release in a separate workflow.")


def _install_system_deps_safe():
    """Safe mode: check what's installed, print instructions for what's missing."""
    import shutil

    print("Checking system dependencies (safe mode — no auto-install)...")

    deps = [
        (
            "gh",
            ["gh"],
            "GitHub CLI",
            "https://cli.github.com — or: apt install gh / brew install gh",
        ),
        ("node", ["node", "npm"], "Node.js", "https://nodejs.org — or: apt install nodejs npm"),
    ]

    missing = []
    for _name, binaries, label, install_hint in deps:
        found = all(shutil.which(binary) for binary in binaries)
        if found:
            print(f"  ✅ {label} already installed")
        else:
            print(f"  -- {label} not found")
            missing.append((label, install_hint))

    if missing:
        print()
        print("  To install missing dependencies manually:")
        for label, hint in missing:
            print(f"    {label}: {hint}")
    else:
        print("  All system dependencies are installed!")


def _install_system_deps_dryrun():
    """Dry-run: just show what would be checked/installed."""
    import shutil

    print("[dry-run] System dependency check:")

    checks = [
        ("gh CLI", ["gh"], "manual OS-native install from https://cli.github.com"),
        ("Node.js", ["node", "npm"], "manual supported-LTS install from https://nodejs.org"),
    ]

    for label, binaries, method in checks:
        found = all(shutil.which(binary) for binary in binaries)
        if found:
            print(f"  ✅ {label}: already installed, skip")
        else:
            print(f"  {label}: would install via: {method}")


def _install_mcporter():
    """Configure Exa only when an already-installed mcporter is available."""
    import shutil
    import subprocess

    print("Setting up mcporter (search backend)...")

    if shutil.which("mcporter"):
        print("  ✅ mcporter already installed")
    else:
        print("  -- mcporter is not installed; no floating global npm install was attempted.")
        print("     Review an exact release, then install mcporter@VERSION separately.")
        return

    # Configure Exa MCP (free, no key needed)
    try:
        r = subprocess.run(
            ["mcporter", "config", "list"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        if "exa" not in r.stdout:
            add_result = subprocess.run(
                ["mcporter", "config", "add", "exa", "https://mcp.exa.ai/mcp"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if add_result.returncode == 0:
                print("  ✅ Exa search configured (free, no API key needed)")
            else:
                print("  [X] mcporter rejected the Exa configuration")
        else:
            print("  ✅ Exa search already configured")
    except Exception:
        print(
            "  [!]  Could not configure Exa. Run manually: mcporter config add exa https://mcp.exa.ai/mcp"
        )

    # NOTE: xhs-cli is now optional, installed via --channels=xiaohongshu


def _install_mcporter_safe():
    """Safe mode: check mcporter status, print instructions."""
    import shutil

    print("Checking mcporter (safe mode)...")

    if shutil.which("mcporter"):
        print("  ✅ mcporter already installed")
        print("  To configure Exa search: mcporter config add exa https://mcp.exa.ai/mcp")
    else:
        print("  -- mcporter not installed")
        print("  Review an exact release, then install mcporter@VERSION separately")
        print("  Then configure Exa: mcporter config add exa https://mcp.exa.ai/mcp")


def _detect_environment():
    """Auto-detect if running on local computer or server."""
    import os

    # Check common server indicators
    indicators = 0

    # SSH session
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"):
        indicators += 2

    # Docker / container
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        indicators += 2

    # No display (headless)
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        indicators += 1

    # Cloud VM identifiers
    for cloud_file in ["/sys/hypervisor/uuid", "/sys/class/dmi/id/product_name"]:
        if os.path.exists(cloud_file):
            try:
                with open(cloud_file) as f:
                    content = f.read().lower()
                if any(
                    x in content
                    for x in [
                        "amazon",
                        "google",
                        "microsoft",
                        "digitalocean",
                        "linode",
                        "vultr",
                        "hetzner",
                    ]
                ):
                    indicators += 2
            except Exception:
                pass

    # systemd-detect-virt
    try:
        import subprocess

        result = subprocess.run(
            ["systemd-detect-virt"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip() != "none":
            indicators += 1
    except Exception:
        pass

    return "server" if indicators >= 2 else "local"


def _cmd_configure(args):
    """Set a config value and test it, or auto-extract from browser."""
    import shutil

    from agent_reach.config import Config

    config = Config()

    # ── Auto-extract from browser ──
    if args.from_browser:
        from agent_reach.cookie_extract import configure_from_browser

        browser = args.from_browser
        print(f"Extracting cookies from {browser}...")
        print()

        results = configure_from_browser(browser, config)

        found_any = False
        for platform, success, message in results:
            if success:
                print(f"  ✅ {platform}: {message}")
                found_any = True
            else:
                print(f"  -- {platform}: {message}")

        print()
        if found_any:
            print("✅ Cookies configured! Run `agent-reach doctor` to see updated status.")
        else:
            print(f"No cookies found. Make sure you're logged into the platforms in {browser}.")
        return

    # ── Manual configure ──
    if not args.key:
        print("Usage: agent-reach configure <key> <value>")
        print("   or: agent-reach configure --from-browser chrome")
        return

    secret_keys = {
        "github-token",
        "groq-key",
        "openai-key",
        "twitter-cookies",
        "xhs-cookies",
    }
    if args.value and args.key in secret_keys:
        print(
            "Refusing a secret on the command line because argv and shell history are observable.",
            file=sys.stderr,
        )
        print(
            f"Use: printf '%s' \"$SECRET\" | agent-reach configure {args.key} --stdin",
            file=sys.stderr,
        )
        return 2

    if args.stdin:
        value = sys.stdin.read().strip()
    elif args.file:
        try:
            value = args.file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            print(f"Could not read {args.file}: {exc}", file=sys.stderr)
            return 2
    elif args.value:
        value = " ".join(args.value)
    elif sys.stdin.isatty():
        prompt = f"{args.key}: "
        value = (
            getpass.getpass(prompt).strip() if args.key in secret_keys else input(prompt).strip()
        )
    else:
        value = ""
    if not value:
        print(f"Missing value for {args.key}")
        return 2

    if args.key == "twitter-cookies":
        # Accept two formats:
        # 1. auth_token ct0 (two separate values)
        # 2. Full cookie header string: "auth_token=xxx; ct0=yyy; ..."
        auth_token, ct0 = _parse_twitter_cookie_input(value)

        if auth_token and ct0:
            config.set("twitter_auth_token", auth_token)
            config.set("twitter_ct0", ct0)

            # Sync credentials to twitter-cli env
            print("✅ Twitter cookies configured!")
            print(
                "  Stored for Agent Reach health checks. For direct twitter-cli use, "
                "export TWITTER_AUTH_TOKEN and TWITTER_CT0 in that process."
            )

            print("Testing Twitter access...", end=" ")
            try:
                import subprocess

                twitter_bin = shutil.which("twitter")
                if not twitter_bin:
                    print("[!] twitter-cli not installed; review and install an exact version")
                else:
                    import os

                    env = os.environ.copy()
                    env["TWITTER_AUTH_TOKEN"] = auth_token
                    env["TWITTER_CT0"] = ct0
                    result = subprocess.run(
                        [twitter_bin, "status"],
                        capture_output=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=15,
                        env=env,
                    )
                    output = (result.stdout or "") + (result.stderr or "")
                    if "ok: true" in output:
                        print("✅ Twitter access works!")
                    else:
                        print("[!] Auth check failed (cookies might be wrong)")
            except Exception as e:
                print(f"[X] Failed: {e}")
        else:
            print("[X] Could not find auth_token and ct0 in your input.")
            print("   Use the hidden prompt, --stdin, or --file with a cookie header/JSON export.")

    elif args.key == "youtube-cookies":
        from agent_reach.utils.paths import set_ytdlp_option

        allowed_browsers = {
            "brave",
            "chrome",
            "chromium",
            "edge",
            "firefox",
            "opera",
            "safari",
            "vivaldi",
        }
        browser = value.lower()
        if browser not in allowed_browsers:
            print(
                f"Unsupported browser {value!r}; choose one of: {', '.join(sorted(allowed_browsers))}",
                file=sys.stderr,
            )
            return 2
        config_path = set_ytdlp_option(
            "--cookies-from-browser",
            f"--cookies-from-browser {browser}",
        )
        print(f"✅ yt-dlp cookie source configured in {config_path}: {browser}")

    elif args.key == "xhs-cookies":
        _configure_xhs_cookies(value)

    elif args.key == "github-token":
        import shutil
        import subprocess

        gh = shutil.which("gh")
        if not gh:
            print("GitHub CLI is not installed; token was not stored.", file=sys.stderr)
            print("Install https://cli.github.com and retry.", file=sys.stderr)
            return 2
        result = subprocess.run(
            [gh, "auth", "login", "--with-token"],
            input=value + "\n",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if result.returncode != 0:
            print("gh rejected the token; no Agent Reach copy was stored.", file=sys.stderr)
            return 2
        config.delete("github_token")
        print("✅ GitHub token stored by gh CLI; Agent Reach kept no copy.")

    elif args.key == "groq-key":
        config.set("groq_api_key", value)
        print("✅ Groq key configured!")

    elif args.key == "openai-key":
        config.set("openai_api_key", value)
        print("✅ OpenAI key configured!")
    return 0


def _cmd_transcribe(args):
    """Transcribe a URL or local audio file via Whisper (Groq → OpenAI fallback)."""
    from pathlib import Path

    from agent_reach.transcribe import TranscribeError, transcribe

    print(
        "Privacy notice: audio is sent to the selected Groq/OpenAI transcription service.",
        file=sys.stderr,
    )
    try:
        text = transcribe(args.source, provider=args.provider)
    except TranscribeError as e:
        print(f"❌ {e}")
        return 1

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"✅ Transcript written to {args.output}")
    else:
        print(text)
    return 0


def _parse_twitter_cookie_input(value: str):
    """Parse Twitter cookie input from either separate values or a cookie header."""
    auth_token = None
    ct0 = None

    if "auth_token=" in value and "ct0=" in value:
        # Full cookie string — parse it.
        for part in value.replace(";", " ").split():
            if part.startswith("auth_token="):
                auth_token = part.split("=", 1)[1]
            elif part.startswith("ct0="):
                ct0 = part.split("=", 1)[1]
    elif len(value.split()) == 2 and "=" not in value:
        # Two separate values: AUTH_TOKEN CT0.
        parts = value.split()
        auth_token = parts[0]
        ct0 = parts[1]

    return auth_token, ct0


def _configure_xhs_cookies(value):
    """Import cookies into xiaohongshu-mcp Docker container.

    Accepts two formats:
    1. Cookie-Editor JSON export (array of cookie objects)
    2. Header String: "name1=value1; name2=value2; ..."

    The xiaohongshu-mcp container stores cookies at $COOKIES_PATH
    (default: /app/data/cookies.json or cookies.json in workdir).
    Format: JSON array of {name, value, domain, path, expires, httpOnly, secure, sameSite}.
    """
    import json
    import shutil
    import subprocess

    value = value.strip()
    if not value:
        print("[X] Missing cookie value.")
        print("   Usage: agent-reach configure xhs-cookies --file <cookies.json>")
        print("      or: agent-reach configure xhs-cookies --stdin  (pipe the cookie JSON)")
        return

    # Detect format and parse
    cookies_json = None

    # Try JSON format first (Cookie-Editor JSON export)
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list) and parsed:
                # Validate it looks like cookie objects
                first = parsed[0]
                if isinstance(first, dict) and "name" in first and "value" in first:
                    cookies_json = json.dumps(parsed)
                    print(f"  Parsed {len(parsed)} cookies from JSON format")
                else:
                    print("[X] JSON array doesn't contain cookie objects (need name/value fields)")
                    return
            else:
                print("[X] Empty or invalid JSON array")
                return
        except json.JSONDecodeError as e:
            print(f"[X] Invalid JSON: {e}")
            return

    # Header String format: "key1=val1; key2=val2; ..."
    if cookies_json is None and "=" in value:
        cookies = []
        for part in value.split(";"):
            part = part.strip()
            if "=" not in part:
                continue
            name, val = part.split("=", 1)
            name = name.strip()
            val = val.strip()
            if name:
                cookies.append(
                    {
                        "name": name,
                        "value": val,
                        "domain": ".xiaohongshu.com",
                        "path": "/",
                        "expires": -1,
                        "size": len(name) + len(val),
                        "httpOnly": False,
                        "secure": False,
                        "session": True,
                        "sameSite": "Lax",
                    }
                )
        if cookies:
            cookies_json = json.dumps(cookies)
            print(f"  Parsed {len(cookies)} cookies from Header String format")
        else:
            print("[X] Could not parse any cookies from input")
            return

    if not cookies_json:
        print("[X] Could not parse cookies. Accepted formats:")
        print('   1. JSON array: \'[{"name":"x","value":"y","domain":".xiaohongshu.com",...}]\'')
        print('   2. Header String: "key1=val1; key2=val2; ..."')
        return

    # Find the container
    docker = shutil.which("docker")
    if not docker:
        # No Docker - write an owner-only local file for manual import.
        from agent_reach.utils.security import atomic_write_private_text

        cookie_path = os.path.expanduser("~/.agent-reach/xhs-cookies.json")
        try:
            atomic_write_private_text(cookie_path, cookies_json)
        except OSError as exc:
            print(f"[X] Could not securely save cookies: {exc}")
            return
        print(f"  Cookies saved to {cookie_path}")
        print("  Docker not found. Copy manually:")
        print(f"  docker cp {cookie_path} xiaohongshu-mcp:/app/data/cookies.json")
        return

    # Check if xiaohongshu-mcp container is running
    try:
        result = subprocess.run(
            [docker, "ps", "--filter", "name=xiaohongshu-mcp", "--format", "{{.Names}}"],
            capture_output=True,
            encoding="utf-8",
            timeout=5,
        )
        container_name = result.stdout.strip()
        if not container_name:
            print("[X] xiaohongshu-mcp container is not running.")
            print("   Start a separately reviewed image pinned by digest, then retry.")
            return
    except Exception as e:
        print(f"[X] Could not check Docker: {e}")
        return

    # Find the cookies path inside the container
    try:
        result = subprocess.run(
            [docker, "exec", container_name, "printenv", "COOKIES_PATH"],
            capture_output=True,
            encoding="utf-8",
            timeout=5,
        )
        cookie_path_in_container = result.stdout.strip()
        if not cookie_path_in_container:
            cookie_path_in_container = "/app/cookies.json"  # fallback: absolute path in workdir
    except Exception:
        cookie_path_in_container = "/app/cookies.json"

    # Write cookies into the container
    tmp_path = None
    try:
        # Write to temp file then docker cp
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(cookies_json)
            tmp_path = f.name
        os.chmod(tmp_path, 0o600)

        result = subprocess.run(
            [docker, "cp", tmp_path, f"{container_name}:{cookie_path_in_container}"],
            capture_output=True,
            encoding="utf-8",
            timeout=10,
        )
        if result.returncode != 0:
            print(f"[X] Failed to copy cookies: {result.stderr}")
            return

        print(f"✅ Cookies written to {container_name}:{cookie_path_in_container}")
        # Restart container so it reloads cookies from disk
        print("  Restarting container to reload cookies...", end=" ", flush=True)
        try:
            restart_result = subprocess.run(
                [docker, "restart", container_name],
                capture_output=True,
                encoding="utf-8",
                timeout=30,
            )
            if restart_result.returncode == 0:
                print("done")
            else:
                print("failed")
                print(f"  Restart manually: docker restart {container_name}")
        except Exception as e:
            print(f"\n  [!] Could not restart container: {e}")
            print(f"  Restart manually: docker restart {container_name}")
    except Exception as e:
        print(f"[X] Failed to write cookies: {e}")
        return
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # Verify login status via mcporter
    mcporter = shutil.which("mcporter")
    if mcporter:
        print("  Verifying login status...", end=" ")
        try:
            result = subprocess.run(
                [mcporter, "call", "xiaohongshu.check_login_status()"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if "已登录" in result.stdout or "logged" in result.stdout.lower():
                print("✅ Login verified!")
            else:
                print("[!] Login check returned unexpected result:")
                print(f"  {result.stdout.strip()[:200]}")
                print("  Cookies were written but login might not be valid. Try fresh cookies.")
        except Exception as e:
            print(f"[!] Could not verify: {e}")
    else:
        print("  (mcporter not found, skipping verification)")


def _cmd_uninstall(args):
    """Remove all Agent Reach config, tokens, and skill files."""
    import shutil
    import subprocess

    dry_run = args.dry_run
    keep_config = args.keep_config

    print()
    print("Agent Reach Uninstaller")
    print("=" * 40)

    if dry_run:
        print("DRY RUN — showing what would be removed (no changes)")
        print()

    removed_any = False

    # ── 1. Config directory (~/.agent-reach/) ──
    config_dir = os.path.expanduser("~/.agent-reach")
    if not keep_config:
        if os.path.isdir(config_dir):
            if dry_run:
                print(f"[dry-run] Would remove config directory: {config_dir}")
                print("          (contains config.yaml with all tokens/cookies/API keys)")
            else:
                try:
                    shutil.rmtree(config_dir)
                    print(f"  Removed config directory: {config_dir}")
                    removed_any = True
                except Exception as e:
                    print(f"  Could not remove {config_dir}: {e}")
        else:
            print(f"  Config directory not found (already clean): {config_dir}")
    else:
        print(f"  Skipping config directory (--keep-config): {config_dir}")

    # ── 2. Skill files ──
    skill_dirs = [
        ("~/.openclaw/skills/agent-reach", "OpenClaw"),
        ("~/.claude/skills/agent-reach", "Claude Code"),
        ("~/.agents/skills/agent-reach", "Agent"),
    ]

    for skill_path_template, platform_name in skill_dirs:
        skill_path = os.path.expanduser(skill_path_template)
        if os.path.isdir(skill_path):
            if dry_run:
                print(f"[dry-run] Would remove {platform_name} skill: {skill_path}")
            else:
                try:
                    if os.path.islink(skill_path):
                        os.unlink(skill_path)
                    else:
                        shutil.rmtree(skill_path)
                    print(f"  Removed {platform_name} skill: {skill_path}")
                    removed_any = True
                except Exception as e:
                    print(f"  Could not remove {skill_path}: {e}")

    # ── 3. mcporter MCP entries ──
    # --keep-config means keep every persisted integration, not only YAML.
    if not keep_config and shutil.which("mcporter"):
        for mcp_name in ("exa", "xiaohongshu"):
            try:
                r = subprocess.run(
                    ["mcporter", "list"],
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                )
                if mcp_name in r.stdout:
                    if dry_run:
                        print(f"[dry-run] Would remove mcporter entry: {mcp_name}")
                    else:
                        remove_result = subprocess.run(
                            ["mcporter", "config", "remove", mcp_name],
                            capture_output=True,
                            encoding="utf-8",
                            errors="replace",
                            timeout=10,
                        )
                        if remove_result.returncode == 0:
                            print(f"  Removed mcporter entry: {mcp_name}")
                            removed_any = True
                        else:
                            print(f"  Could not remove mcporter entry: {mcp_name}")
            except Exception:
                pass

    # ── 4. Summary and optional steps ──
    print()
    if dry_run:
        print("Dry run complete. No changes were made.")
        print("Run without --dry-run to actually remove the above.")
    else:
        if removed_any:
            print("Agent Reach data removed.")
        else:
            print("Nothing to remove — already clean.")

    print()
    print("Optional: remove the Agent Reach Python package itself:")
    print("  pip uninstall agent-reach")
    print()
    print("Optional: remove tools installed by Agent Reach:")
    print("  npm uninstall -g mcporter")
    print("  pipx uninstall twitter-cli")
    print("  npm uninstall -g undici")


def _cmd_doctor(args=None):
    from agent_reach.config import Config
    from agent_reach.doctor import check_all, format_report

    rich_print: Any = None
    try:
        from rich import print as imported_rich_print

        rich_print = imported_rich_print
    except ImportError:
        pass
    config = Config(create=False)
    results = check_all(config)

    if args is not None and getattr(args, "json", False):
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if rich_print is not None:
        rich_print(format_report(results))
    else:
        print(format_report(results))

    return 0


def _cmd_setup():
    from agent_reach.config import Config

    config = Config()
    print()
    print("Agent Reach Setup")
    print("=" * 40)
    print()

    # Step 1: Exa (via mcporter, no API key required)
    import shutil
    import subprocess

    print("【推荐】全网搜索 — Exa（通过 mcporter）")
    print("  免费，无需 API Key")

    if not shutil.which("mcporter"):
        print("  当前状态: -- mcporter 未安装")
        print("  请先审阅并另行安装固定的 mcporter@VERSION")
        print("  然后：mcporter config add exa https://mcp.exa.ai/mcp")
        print()
    else:
        try:
            r = subprocess.run(
                ["mcporter", "config", "list"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if "exa" in r.stdout.lower():
                print("  当前状态: ✅ 已配置")
            else:
                print("  当前状态: -- 未配置")
                setup_now = input("  现在自动配置 Exa 吗？[Y/n]: ").strip().lower()
                if setup_now in ("", "y", "yes"):
                    add_r = subprocess.run(
                        ["mcporter", "config", "add", "exa", "https://mcp.exa.ai/mcp"],
                        capture_output=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=10,
                    )
                    if add_r.returncode == 0:
                        print("  ✅ Exa 已配置")
                    else:
                        print("  [!] 自动配置失败，请手动执行：")
                        print("     mcporter config add exa https://mcp.exa.ai/mcp")
        except Exception:
            print("  [!] 无法检查 Exa 配置，请手动执行：")
            print("     mcporter config add exa https://mcp.exa.ai/mcp")
        print()

    # Step 2: GitHub token
    print("【可选】GitHub Token — 提高 API 限额")
    print("  无 token: 60 次/小时 | 有 token: 5000 次/小时")
    print("  获取: https://github.com/settings/tokens (无需任何权限)")
    current = config.get("github_token")
    if current:
        print("  当前状态: ✅ 已配置")
    else:
        key = getpass.getpass("  GITHUB_TOKEN (回车跳过): ").strip()
        if key:
            import shutil

            gh = shutil.which("gh")
            if gh:
                result = subprocess.run(
                    [gh, "auth", "login", "--with-token"],
                    input=key + "\n",
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                if result.returncode == 0:
                    print("  ✅ Token 已由 gh CLI 安全保存")
                else:
                    print("  [!] gh 拒绝了 Token；Agent Reach 未保存副本")
            else:
                print("  [!] gh CLI 未安装；Agent Reach 未保存 Token")
        else:
            print("  跳过。公开 API 也能用")
    print()

    # Step 3: Reddit — rdt-cli
    print("【信息】Reddit — 必须登录态（无零配置路径）。桌面推荐 OpenCLI；或 rdt-cli：")
    print(f"  安装：pipx install '{_RDT_GIT_SOURCE}'")
    print("  然后运行：rdt login（需先在浏览器登录 reddit.com）")
    print()

    # Step 4: Groq (Whisper)
    print("【可选】Groq API — 视频无字幕时的语音转文字")
    print("  免费额度，注册: https://console.groq.com")
    current = config.get("groq_api_key")
    if current:
        print("  当前状态: ✅ 已配置")
    else:
        key = getpass.getpass("  GROQ_API_KEY (回车跳过): ").strip()
        if key:
            config.set("groq_api_key", key)
            print("  ✅ 语音转文字已开启！")
        else:
            print("  跳过")
    print()

    # Summary
    print("=" * 40)
    print(f"✅ 配置已保存到 {config.config_path}")
    print("运行 agent-reach doctor 查看完整状态")
    print()


def _classify_update_error(exc):
    """Classify update-check errors for user-friendly diagnostics."""
    import requests

    if isinstance(exc, requests.exceptions.Timeout):
        return "timeout"
    if isinstance(exc, requests.exceptions.ConnectionError):
        msg = str(exc).lower()
        dns_markers = [
            "name or service not known",
            "temporary failure in name resolution",
            "nodename nor servname",
            "getaddrinfo failed",
            "name resolution",
            "dns",
        ]
        if any(marker in msg for marker in dns_markers):
            return "dns"
        return "connection"
    if isinstance(exc, requests.exceptions.HTTPError):
        return "http"
    return "unknown"


def _update_error_text(kind):
    """Map internal error kinds to user-facing text."""
    mapping = {
        "timeout": "网络超时",
        "dns": "DNS 解析失败",
        "rate_limit": "GitHub API 速率限制",
        "connection": "网络连接失败",
        "server_error": "GitHub 服务暂时不可用",
        "http": "HTTP 请求失败",
        "unknown": "未知网络错误",
    }
    return mapping.get(kind, "请求失败")


def _classify_github_response_error(resp):
    """Classify non-200 GitHub responses that merit special handling."""
    if resp is None:
        return "unknown"
    if resp.status_code == 429:
        return "rate_limit"
    if resp.status_code == 403:
        remaining = resp.headers.get("X-RateLimit-Remaining", "")
        if remaining == "0":
            return "rate_limit"
        try:
            message = resp.json().get("message", "").lower()
            if "rate limit" in message:
                return "rate_limit"
        except Exception:
            pass
    if 500 <= resp.status_code < 600:
        return "server_error"
    return None


def _github_get_with_retry(url, timeout=10, retries=3, sleeper=time.sleep):
    """GET GitHub API with retry/backoff and basic error classification."""
    import requests

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            if attempt >= retries:
                return None, _classify_update_error(exc), attempt
            sleeper(2 ** (attempt - 1))
            continue

        err_kind = _classify_github_response_error(resp)
        if err_kind in ("rate_limit", "server_error"):
            if attempt >= retries:
                return None, err_kind, attempt
            delay = 2 ** (attempt - 1)
            retry_after = resp.headers.get("Retry-After")
            if err_kind == "rate_limit" and retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except Exception:
                    pass
            sleeper(delay)
            continue

        return resp, None, attempt

    return None, "unknown", retries


#: Full update = package + upstream tools + skill. The one-liner walks an
#: agent through all three (docs/update.md); bare pip only updates the package.
_UPDATE_INSTRUCTIONS = (
    "审阅目标发布版本后更新本体（替换 VERSION）：\n"
    '  python -m pip install "agent-reach==VERSION"\n'
    "然后显式同步 skill（会保护本地定制）：\n"
    "  agent-reach skill --install"
)


def _is_newer_version(remote: str, local: str) -> bool:
    """True if remote is strictly newer than local (semantic compare).

    A plain != would tell users "update available" when their local build is
    AHEAD of the latest release (e.g. installed from main during a release
    window) — and walk them into a downgrade.
    """

    def parse(v):
        try:
            return tuple(int(x) for x in v.strip().split("."))
        except ValueError:
            return None

    remote_parts, local_parts = parse(remote), parse(local)
    if remote_parts is None or local_parts is None:
        return remote != local  # unparseable — fall back to old behavior
    return remote_parts > local_parts


def _cmd_check_update():
    """Check for newer versions on GitHub."""
    from agent_reach import __version__

    print(f"当前版本: v{__version__}")
    release_url = "https://api.github.com/repos/Panniantong/Agent-Reach/releases/latest"
    commit_url = "https://api.github.com/repos/Panniantong/Agent-Reach/commits/main"

    # Fetch latest release with retry/backoff.
    resp, err, attempts = _github_get_with_retry(release_url, timeout=10, retries=3)
    if err:
        print(f"[!] 无法检查更新（{_update_error_text(err)}，已重试 {attempts} 次）")
        return "error"

    if resp.status_code == 200:
        data = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        body = data.get("body", "")

        if latest and _is_newer_version(latest, __version__):
            print(f"最新版本: v{latest} ← 有更新！")
            if body:
                print()
                print("更新内容：")
                # Show first 20 lines of release notes
                for line in body.strip().split("\n")[:20]:
                    print(f"  {line}")
            print()
            print(_UPDATE_INSTRUCTIONS)
            return "update_available"
        print("✅ 已是最新版本")
        return "up_to_date"

    release_err = _classify_github_response_error(resp)
    if release_err == "rate_limit":
        print("[!] 无法检查更新（GitHub API 速率限制，请稍后重试）")
        return "error"

    # No releases yet, fall back to latest main commit.
    resp2, err2, attempts2 = _github_get_with_retry(commit_url, timeout=10, retries=2)
    if err2:
        print(f"[!] 无法检查更新（{_update_error_text(err2)}，已重试 {attempts + attempts2} 次）")
        return "error"
    if resp2.status_code == 200:
        commit = resp2.json()
        sha = commit.get("sha", "")[:7]
        msg = commit.get("commit", {}).get("message", "").split("\n")[0]
        date = commit.get("commit", {}).get("committer", {}).get("date", "")[:10]
        print(f"最新提交: {sha} ({date}) {msg}")
        print()
        print(_UPDATE_INSTRUCTIONS)
        return "unknown"

    commit_err = _classify_github_response_error(resp2)
    if commit_err == "rate_limit":
        print("[!] 无法检查更新（GitHub API 速率限制，请稍后重试）")
        return "error"

    print(f"[!] 无法检查更新（GitHub 返回 {resp2.status_code}）")
    return "error"


def _cmd_watch(args=None):
    """Quick health check + update check, designed for scheduled tasks.

    Only outputs problems. If everything is fine, outputs a single line.
    """
    from agent_reach import __version__
    from agent_reach.config import Config
    from agent_reach.doctor import check_all

    record_baseline = bool(getattr(args, "record_baseline", False))
    config = Config(create=record_baseline)
    issues = []

    # Check channels
    results = check_all(config)
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    requested = {item.strip() for item in getattr(args, "channels", "").split(",") if item.strip()}
    saved_channels = config.get("watch_channels", [])
    baseline = config.get("watch_baseline", {})
    if not isinstance(saved_channels, list):
        saved_channels = []
    if not isinstance(baseline, dict):
        baseline = {}
    monitored = requested or set(saved_channels) or set(baseline)
    if not monitored:
        # No false "regression" claim: first run checks only core channels.
        monitored = {key for key, result in results.items() if result["tier"] == 0}

    unknown = monitored - set(results)
    for key in sorted(unknown):
        issues.append(f"[X] 未知渠道：{key}")

    for key in sorted(monitored & set(results)):
        result = results[key]
        previous = baseline.get(key)
        if result["status"] == "ok":
            continue
        prefix = "[X]" if result["status"] in ("off", "error") else "[!]"
        if previous == "ok":
            label = "基线回归"
        else:
            label = "当前不可用"
        issues.append(f"{prefix} {label} — {result['name']}：{result['message']}")

    if record_baseline:
        selected = sorted(monitored & set(results))
        config.set("watch_channels", selected)
        config.set(
            "watch_baseline",
            {key: results[key]["status"] for key in selected},
        )
        print(f"Recorded watch baseline for {len(selected)} channels.")

    # Check for updates
    update_status = "unknown"
    new_version = ""
    release_body = ""
    resp, err, _attempts = _github_get_with_retry(
        "https://api.github.com/repos/Panniantong/Agent-Reach/releases/latest",
        timeout=10,
        retries=2,
    )
    if not err and resp and resp.status_code == 200:
        data = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        if latest and _is_newer_version(latest, __version__):
            update_status = "available"
            new_version = latest
            release_body = data.get("body", "")
        elif latest:
            update_status = "current"

    # Output
    if not issues and update_status == "current":
        print(f"Agent Reach: 全部正常（监控渠道；{ok}/{total} 渠道可用，v{__version__} 已是最新）")
        return 0
    if update_status == "unknown":
        issues.append("[!] 版本状态未知：更新检查失败")

    print("Agent Reach 监控报告")
    print("=" * 40)
    print(f"版本: v{__version__}  |  渠道: {ok}/{total}")

    if issues:
        print()
        for issue in issues:
            print(f"  {issue}")

    if update_status == "available":
        print()
        print(f"新版本可用: v{new_version}")
        if release_body:
            for line in release_body.strip().split("\n")[:10]:
                print(f"    {line}")
        print(_UPDATE_INSTRUCTIONS)
    return 2 if update_status == "unknown" else 1


if __name__ == "__main__":
    main()
