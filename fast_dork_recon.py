import asyncio
import aiohttp
import requests
import re
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_FILE = "canli_siteler.txt"

DORK_POOL = [
    'inurl:"/view/view.shtml"',
    'intitle:"Live View / - AXIS"',
    'inurl:"ViewerFrame?Mode="',
    'inurl:"/webcapture.htm"',
    'inurl:"/cgi-bin/guestimage.html"',
    'intitle:"Network Camera" inurl:"/index.html"',
    'inurl:"/mjpg/video.mjpg"',
    'intitle:"webcamXP 5"'
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

processed_urls = set()

def test_connection():
    """Betiğin başında dış dünyaya ve arama motoruna istek gidip gitmediğini doğrular."""
    print("\n[*] BAĞLANTI TESTİ BAŞLATILIYOR...")
    try:
        # 1. Genel İnternet Bağlantı Testi
        test_ip = requests.get("http://httpbin.org/ip", headers=HEADERS, timeout=5)
        my_ip = test_ip.json().get("origin", "Bilinmiyor")
        print(f"\033[92m[+] İnternet Bağlantısı Aktif! Dış IP Adresiniz: {my_ip}\033[0m")
        
        # 2. Arama Motoru (DuckDuckGo) Erişim Testi
        ddg_test = requests.post("https://html.duckduckgo.com/html/", data={'q': 'test'}, headers=HEADERS, timeout=5)
        if ddg_test.status_code == 200:
            print(f"\033[92m[+] Arama Motoru Erişimi Başarılı! (Status: 200 OK)\033[0m\n")
            return True
        else:
            print(f"\033[91m[!] Arama Motoru Engeli veya Hata! (Status: {ddg_test.status_code})\033[0m\n")
            return False
    except Exception as e:
        print(f"\033[91m[!] Bağlantı Testi Başarısız: {e}\033[0m\n")
        return False

def fetch_ddg_urls(dork, page=1):
    """DuckDuckGo üzerinden arama yapar ve IP tabanlı HTTP bağlantılarını süzer."""
    urls = set()
    try:
        url = "https://html.duckduckgo.com/html/"
        data = {'q': dork, 's': str((page - 1) * 30)}
        
        response = requests.post(url, data=data, headers=HEADERS, timeout=10)
        
        matches = re.findall(r'class="result__url" href="([^"]+)"', response.text)
        for m in matches:
            clean_url = m
            if "//duckduckgo.com/l/?" in clean_url:
                match_uddg = re.search(r'uddg=([^&]+)', clean_url)
                if match_uddg:
                    clean_url = requests.utils.unquote(match_uddg.group(1))
            
            if clean_url.startswith("http://") and clean_url not in processed_urls:
                if not re.search(r'\.(com|net|org|gov|edu|uk|de|fr|tr)\b', clean_url):
                    urls.add(clean_url)
                    processed_urls.add(clean_url)
    except Exception:
        pass
    return urls

async def check_and_save_url(session, url, semaphore, file_handle):
    """URL canlılığını sorgular; 200 OK yanıtlarını yeşil, diğerlerini kırmızı basar."""
    async with semaphore:
        try:
            async with session.get(url, headers=HEADERS, ssl=False, timeout=6, allow_redirects=True) as response:
                final_url = str(response.url)
                
                if final_url.startswith("https://"):
                    print(f"\033[91m[-] BULUNAMADI (HTTPS Yönlendirmesi) -> {url}\033[0m")
                    sys.stdout.flush()
                    return

                if response.status == 200:
                    print(f"\033[92m[+] CANLI HTTP (200 OK) -> {url}\033[0m")
                    sys.stdout.flush()
                    file_handle.write(url + "\n")
                    file_handle.flush()
                else:
                    print(f"\033[91m[-] BULUNAMADI (Status: {response.status}) -> {url}\033[0m")
                    sys.stdout.flush()
        except Exception:
            print(f"\033[91m[-] BULUNAMADI (Zaman Aşımı / Kapalı) -> {url}\033[0m")
            sys.stdout.flush()

async def start_recon():
    print("=" * 60)
    print("      OPTIMIZED IP/CAMERA DORK RECON ENGINE WITH TEST       ")
    print("=" * 60)

    # Önce Istek Testi Çalıştırılır
    if not test_connection():
        print("[!] İstekler dış dünyaya ulaşamadığı için tarama başlatılamıyor.")
        return

    print(f"[*] Canlı sonuçlar anlık olarak '{OUTPUT_FILE}' dosyasına yazılıyor...\n")

    semaphore = asyncio.Semaphore(10)
    dork_index = 0
    page = 1

    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_file:
        async with aiohttp.ClientSession() as session:
            try:
                while True:
                    current_dork = DORK_POOL[dork_index % len(DORK_POOL)]
                    print(f"\n\033[94m[*] Taranıyor [Dork #{dork_index + 1} | Sayfa {page}]: {current_dork}\033[0m")
                    
                    raw_urls = fetch_ddg_urls(current_dork, page=page)
                    
                    if raw_urls:
                        print(f"[+] {len(raw_urls)} adet HTTP IP adresi bulundu, canlılık sorgulanıyor...\n")
                        tasks = [check_and_save_url(session, url, semaphore, out_file) for url in raw_urls]
                        await asyncio.gather(*tasks)
                    else:
                        print("\033[91m[-] BULUNAMADI (Bu sayfada uygun IP/HTTP sonucu dönmedi)\033[0m")

                    page += 1
                    
                    if page > 2:
                        page = 1
                        dork_index += 1
                        
                    await asyncio.sleep(2)

            except KeyboardInterrupt:
                print("\n\n\033[93m[!] Tarama kullanıcı tarafından durduruldu.\033[0m")
                print(f"[+] Toplam işlenen benzersiz URL: {len(processed_urls)}")
                print(f"[+] Canlılar '{OUTPUT_FILE}' dosyasına kaydedildi.")

if __name__ == "__main__":
    asyncio.run(start_recon())
