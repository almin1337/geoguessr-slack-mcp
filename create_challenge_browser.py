#!/usr/bin/env python3
"""
Create a GeoGuessr challenge via browser automation.

Auth: use GEOGUESSR_COOKIE in .env, or pass cookie=..., or pass email= + password=
to log in via the sign-in form.

Setup:
  pip install playwright
  playwright install chromium

Flow (cookie): inject _ncfa → map page → Challenge → Play → Create Challenge.
Flow (credentials): /signin → fill email/password → submit → map page → same as above.
"""

import argparse
import os
import re
import sys
from urllib.parse import urljoin

from dotenv import load_dotenv

load_dotenv()

GEOGUESSR_COOKIE = os.getenv("GEOGUESSR_COOKIE")
SIGNIN_URL = "https://www.geoguessr.com/signin"


def _login_with_credentials(page, email: str, password: str, slow_mo: int = 0) -> bool:
    """Fill and submit the GeoGuessr sign-in form. Returns True if login succeeded."""
    page.goto(SIGNIN_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)

    # Email field
    email_filled = False
    for sel in [
        'input[type="email"]',
        'input[name="email"]',
        'input[placeholder*="mail" i]',
        'input[placeholder*="Email" i]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.fill(email)
                email_filled = True
                break
        except Exception:
            continue
    if not email_filled:
        try:
            page.get_by_label("Email", exact=False).fill(email)
            email_filled = True
        except Exception:
            pass
    if not email_filled:
        print("ERROR: Could not find email input on sign-in page")
        return False

    # Password field
    password_filled = False
    for sel in [
        'input[type="password"]',
        'input[name="password"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.fill(password)
                password_filled = True
                break
        except Exception:
            continue
    if not password_filled:
        try:
            page.get_by_label("Password", exact=False).fill(password)
            password_filled = True
        except Exception:
            pass
    if not password_filled:
        print("ERROR: Could not find password input on sign-in page")
        return False

    page.wait_for_timeout(500)

    # Log in button
    login_clicked = False
    for sel in [
        'button:has-text("Log in")',
        'button:has-text("LOG IN")',
        'button[type="submit"]',
        'input[type="submit"]',
        'a:has-text("Log in")',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click(timeout=5000)
                login_clicked = True
                break
        except Exception:
            continue
    if not login_clicked:
        print("ERROR: Could not find Log in button")
        return False

    # Wait for navigation away from signin (or for error message)
    page.wait_for_timeout(3000)
    try:
        page.wait_for_url(lambda u: "/signin" not in u, timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    # Success = we're not on signin and we have session (e.g. cookie or redirect to home/me)
    current = page.url
    if "/signin" in current:
        # Check for error message
        err = page.locator('[role="alert"], .error, [class*="error"]').first
        try:
            if err.is_visible(timeout=1000):
                print("Login error:", err.text_content())
        except Exception:
            pass
        return False
    print("Login succeeded")
    return True


def create_challenge_via_browser(
    map_slug: str = "world",
    rounds: int = 5,
    time_per_round: int = 90,
    headed: bool = False,
    slow_mo: int = 0,
    cookie: str | None = None,
    email: str | None = None,
    password: str | None = None,
) -> tuple[str, str | None] | None:
    """
    Create a GeoGuessr challenge by automating the browser.

    Auth (use one of):
    - cookie: _ncfa value, or set GEOGUESSR_COOKIE in .env
    - email + password: log in via the sign-in form, then create challenge

    Returns the challenge URL if successful, None otherwise.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed. Run: pip install playwright")
        return None

    use_credentials = email and password
    auth_cookie = None if use_credentials else (cookie or GEOGUESSR_COOKIE)

    if not use_credentials and not auth_cookie:
        print("ERROR: Provide cookie (or GEOGUESSR_COOKIE) or both email and password.")
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(
            base_url="https://www.geoguessr.com",
            viewport={"width": 1280, "height": 800},
        )

        if auth_cookie:
            context.add_cookies([
                {
                    "name": "_ncfa",
                    "value": auth_cookie,
                    "domain": ".geoguessr.com",
                    "path": "/",
                }
            ])

        page = context.new_page()
        if slow_mo:
            page.set_default_timeout(30000)

        try:
            if use_credentials:
                if not _login_with_credentials(page, email, password, slow_mo):
                    return None
                page.wait_for_timeout(1500)

            # Navigate to map page
            url = f"/maps/{map_slug}"
            print(f"Navigating to https://www.geoguessr.com{url} ...")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=15000)

            # Wait for content
            page.wait_for_timeout(3000)

            # Maps page: mode pills (single | challenge | play along) + Play button
            # Click "challenge" mode (exact to avoid "Create Challenge")
            challenge_clicked = False
            try:
                el = page.get_by_text("challenge", exact=True).first
                if el.is_visible(timeout=3000):
                    el.click(timeout=3000)
                    challenge_clicked = True
                    print("Clicked challenge mode")
            except Exception:
                pass
            if not challenge_clicked:
                try:
                    el = page.locator('a[href*="challenge"], [role="tab"]:has-text("challenge")').first
                    if el.is_visible(timeout=2000):
                        el.click(timeout=3000)
                        challenge_clicked = True
                        print("Clicked challenge tab/link")
                except Exception:
                    pass
            if not challenge_clicked:
                try:
                    link = page.locator('a[href*="challenge"]').first
                    if link.is_visible(timeout=2000):
                        link.click()
                        challenge_clicked = True
                        print("Clicked challenge link")
                except Exception:
                    pass

            page.wait_for_timeout(2000)

            # Click Play to open the game/challenge modal (playButtons container)
            play_clicked = False
            try:
                play = page.locator('[class*="playButtons"]').first
                if play.is_visible(timeout=3000):
                    play.click()
                    play_clicked = True
                    print("Clicked playButtons")
                    page.wait_for_timeout(2500)
            except Exception:
                pass
            if not play_clicked:
                try:
                    play = page.locator('button:has-text("Play"), a:has-text("Play")').first
                    if play.is_visible(timeout=3000):
                        play.click()
                        print("Clicked Play")
                        page.wait_for_timeout(2500)
                except Exception:
                    pass

            # Look for Create Challenge button (in modal or page)
            create_clicked = False
            for sel in [
                'button:has-text("Create Challenge")',
                'button:has-text("CREATE CHALLENGE")',
                '[data-cy="create-challenge"]',
                'button:has-text("Create")',
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click(timeout=3000)
                        create_clicked = True
                        print("Clicked Create Challenge")
                        break
                except Exception:
                    continue

            page.wait_for_timeout(5000)

            def _get_session_cookie() -> str | None:
                if not use_credentials:
                    return None
                for c in context.cookies():
                    if c.get("name") == "_ncfa":
                        return c.get("value")
                return None

            # Extract challenge URL from current URL or page
            current_url = page.url
            if "/challenge/" in current_url:
                match = re.search(r"(https?://[^/]+/challenge/[a-zA-Z0-9_-]+)", current_url)
                url = match.group(1) if match else current_url
                return (url, _get_session_cookie())

            # Check for share link or redirect
            page.wait_for_timeout(3000)
            final_url = page.url
            if "/challenge/" in final_url:
                match = re.search(r"(https?://[^/]+/challenge/[a-zA-Z0-9_-]+)", final_url)
                url = match.group(1) if match else final_url
                return (url, _get_session_cookie())

            # Look for challenge link in page
            links = page.locator('a[href*="/challenge/"]').all()
            for link in links:
                href = link.get_attribute("href")
                if href and "/challenge/" in href:
                    url = urljoin("https://www.geoguessr.com", href)
                    return (url, _get_session_cookie())

            return None

        finally:
            context.close()
            browser.close()


def main():
    parser = argparse.ArgumentParser(description="Create GeoGuessr challenge via browser automation")
    parser.add_argument("--map", "-m", default="world", help="Map slug")
    parser.add_argument("--rounds", "-r", type=int, default=5)
    parser.add_argument("--time", "-t", type=int, default=90, help="Seconds per round")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--slow", type=int, default=0, help="Slow down by N ms per action")
    parser.add_argument("--email", "-e", help="Log in with email (use with --password)")
    parser.add_argument("--password", "-p", help="Log in with password (use with --email)")
    args = parser.parse_args()

    if (args.email and not args.password) or (args.password and not args.email):
        parser.error("Provide both --email and --password to log in with credentials.")
    use_creds = bool(args.email and args.password)

    print("Creating GeoGuessr challenge via browser automation...")
    print(f"Map: {args.map} | Rounds: {args.rounds} | Time: {args.time}s per round")
    if use_creds:
        print("Auth: email/password (sign-in form)")
    else:
        print("Auth: cookie (GEOGUESSR_COOKIE)")
    print("(Note: Game settings like time/rounds may need to be set in the modal)")
    print()

    result = create_challenge_via_browser(
        map_slug=args.map,
        rounds=args.rounds,
        time_per_round=args.time,
        headed=args.headed,
        slow_mo=args.slow,
        email=args.email if use_creds else None,
        password=args.password if use_creds else None,
    )

    if result:
        url = result[0] if isinstance(result, tuple) else result
        print(f"\n✅ Challenge created!\n{url}")
        return 0
    print("\n❌ Could not create challenge.")
    print("  Try --headed to watch the browser and debug.")
    if use_creds:
        print("  Check email/password and that the sign-in page hasn’t changed.")
    else:
        print("  Ensure: 1) GEOGUESSR_COOKIE is set  2) playwright install chromium  (if needed)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
