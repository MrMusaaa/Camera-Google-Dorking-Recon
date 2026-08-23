#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import re
import json
import os
import sys
import time
import signal
import urllib.parse
from datetime import datetime
from urllib.parse import urlparse, quote, unquote
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init
from fake_useragent import UserAgent
from tqdm import tqdm
import random
import hashlib
import socket
import ssl

init(autoreset=True)

# ============================================================
# KONFİGÜRASYON
# ============================================================
CONFIG = {
    "max_concurrent": 50,
    "timeout": 10,
    "max_retries": 3,
    "output_file": "canli_siteler.txt",
    "backup_file": "canli_siteler_backup.txt",
    "log_file": "recon_log.txt",
    "debug": False,
    "max_results_per_dork": 30,
    "request_delay": 0.5
}

# ============================================================
# GLOBAL DEĞİŞKENLER - CTRL+C için
# ============================================================
running = True
bot_instance = None
found_urls_buffer = []
found_camera_urls = []
alive_urls_list = []

# ============================================================
# SİNYAL YAKALAMA - CTRL+C
# ============================================================
def signal_handler(sig, frame):
    global running, bot_instance, found_urls_buffer, alive_urls_list
    print(Fore.YELLOW + "\n\n⚠ CTRL+C tespit edildi! Veriler kaydediliyor...")
    running = False
    
    try:
        # Tüm bulunan URL'leri kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"canli_siteler_{timestamp}.txt"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"# Fast Dork Recon Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ===========================================\n\n")
            
            # Canlı URL'ler
            f.write("# CANLI URL'LER\n")
            for url_data in alive_urls_list:
                f.write(f"{url_data['url']} | Status: {url_data['status']} | Type: {url_data['content_type']} | Time: {url_data['timestamp']}\n")
            
            f.write("\n# TESPİT EDİLEN KAMERA URL'LERİ\n")
            for url in found_camera_urls:
                f.write(f"{url}\n")
        
        # Ana dosyaya da kaydet
        with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
            f.write(f"\n# --- CTRL+C ile sonlandırıldı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            for url_data in alive_urls_list:
                f.write(f"{url_data['url']} | Status: {url_data['status']} | Type: {url_data['content_type']} | Time: {url_data['timestamp']}\n")
        
        print(Fore.GREEN + f"\n✅ Veriler kaydedildi: {backup_file}")
        print(Fore.GREEN + f"✅ Ana dosyaya eklendi: {CONFIG['output_file']}")
        print(Fore.GREEN + f"📊 Toplam canlı URL: {len(alive_urls_list)}")
        print(Fore.GREEN + f"📊 Toplam tespit edilen URL: {len(found_camera_urls)}")
        
        if bot_instance and hasattr(bot_instance, 'health_checker'):
            stats = bot_instance.health_checker.get_statistics()
            print(Fore.WHITE + f"📊 İstatistikler - Canlı: {stats['alive']} | Kapalı: {stats['dead']} | Toplam: {stats['total']}")
        
        sys.exit(0)
        
    except Exception as e:
        print(Fore.RED + f"❌ Kaydetme hatası: {e}")
        sys.exit(1)

# Sinyal handler'ı kaydet
signal.signal(signal.SIGINT, signal_handler)

# ============================================================
# DORK LİSTESİ - Google Dorks
# ============================================================
GOOGLE_DORKS = [
    'inurl:"CgiStart?page="',
    'inurl:camctrl.cgi',
    'inurl:"view/index.shtml"',
    'intitle:"IP CAMERA Viewer" intext:"setting | Client setting"',
    'intitle:"webcam 7" inurl:"/gallery.html"',
    'intitle:"yawcam" inurl:":8081"',
    'intitle:"iGuard Fingerprint Security System"',
    'intitle:"Edr1680 remote viewer"',
    'intitle:"NetCam Live Image" -.edu -.gov',
    'intitle:"WEBDVR" -inurl:product -inurl:demo',
    'intitle:"AXIS 240 Camera Server" intext:"server push" -help',
    'intitle:"active webcam page"',
    'inurl:"MultiCameraFrame?Mode=Motion"',
    'intitle:"webcamXP 5" -download',
    'inurl:"/view/view.shtml?id="',
    'inurl:/view/viewer_index.shtml',
    'intext:"powered by webcamXP 5"',
    'intitle:"Live View /- AXIS" |inurl:view/view.shtml',
    'allintitle:Axis 2.10 OR 2.12 OR 2.30 OR 2.31 OR 2.32 OR 2.33 OR 2.34 OR 2.40 OR 2.42 OR 2.43 "Network Camera"',
    'intitle:"BlueNet Video Viewer"',
    'intitle:"SNC-RZ30" -demo',
    'inurl:cgi-bin/guestimage.html',
    'intitle:"Veo Observer XT"',
    'intitle:"webcamXP 5"',
    'inurl:"lvappl.htm"',
    'inurl:/view.shtml',
    'intitle:"Live View/ — AXIS"',
    'inurl:iview/view.shtml',
    'inurl:ViewerFrame?M0de=',
    'inurl:axis-cgi/jpg',
    'inurl:axis-cgi/mjpg',
    'inurl:view/indexFrame.shtml',
    'liveapplet',
    'intitle:"live view" intitle:axis',
    'intitle:liveapplet inurl:LvAppl',
    'intitle:"Live View/ — AXIS 206M"',
    'inurl:indexFrame.shtml Axis',
    'intitle:start inurl:cgistart',
    'intitle:"WJ-NTI 04 Main Page"',
    'intitle:snc-220 inurl:home/',
    'intitle:"Toshiba Network Camera" user login',
    'intitle:"netcam live image"',
    'intitle:"i-Catcher Console - Web Monitor"',
    'intitle:"IP Webcam" inurl:"/greet.html"',
    'intitle:"NetCamSC*" | intitle:"NetCamXL*" inurl:index.html',
    'inurl:"live/cam.html"',
    'inurl:/config/cam_portal.cgi "Panasonic"',
    '"Camera Live Image" inurl:"guestimage.html"',
    'intitle:"webcam" inurl:login',
    'inurl:/ViewerFrame? intitle:"Network Camera NetworkCamera"',
    'intitle:"WEBCAM 7 " -inurl:/admin.html',
    'intitle:NetworkCamera intext:"Pan / Tilt" inurl:ViewerFrame',
    'inurl:/live.htm intext:"M-JPEG"|"System Log"|"Camera-1"|"View Control"',
    'intitle:"webcamXP 5" inurl:8080 "Live"',
    'inurl:"MultiCameraFrame?Mode=Motion"',
    'intitle:"Weather Wing WS-2"',
    'intitle:"Live View /- AXIS" OR inurl:view/view.shtml OR inurl:view/indexFrame.shtml',
    'intitle:"Network Camera" inurl:"/main.cgi"',
    'inurl:index.html "Network Camera" intitle:"Live View"',
    'inurl:main.cgi inurl:user inurl:password',
    'intitle:"IP Camera" inurl:viewer',
    'inurl:snapshot.cgi inurl:username',
    'intitle:"webcam 7" inurl:8080 -intitle:"webcam 7"',
    'intitle:"IP CAMERA Viewer" intext:"setting | Client setting"',
    'intitle:"Device(" AND intext:"Network Camera" AND "language:" "AND "Password"',
    'inurl:"CgiStart?page=" inurl:cam'
]

# ============================================================
# SHODAN BENZERİ DORKLAR
# ============================================================
SHODAN_STYLE_DORKS = [
    'product:"Hikvision IP Camera"',
    'product:"D-Link IP Camera"',
    'product:"Axis Network Camera"',
    'product:"Foscam IP Camera"',
    'product:"Vivotek Network Camera"',
    'product:"Dahua IP Camera"',
    'product:"Sony Network Camera"',
    'product:"Panasonic Network Camera"',
    'product:"ACTi IP Camera"',
    'product:"Arecont Vision Camera"',
    'product:"IQinVision Camera"',
    'product:"Mobotix Camera"',
    'product:"Netwave IP Camera"',
    'product:"TP-Link IP Camera"',
    'product:"Lilin IP Camera"',
    'product:"Speco IP Camera"',
    'product:"Avigilon Camera"',
    'product:"Geovision Camera"',
    'product:"EverFocus Camera"',
    'product:"Dedicated Micros Camera"',
    'product:"Canon VB Camera"',
    'product:"NetCamXL"',
    'product:"NetCamSC"',
    'product:"MotionEYE"',
    'product:"Webcam 7"',
    'product:"webcamXP"',
    'Server: SQ-WEBCAM',
    'Server: yawcam',
    'Server: uc-httpd',
    'title:camera',
    'title:"Webcam"',
    'has_screenshot:true',
    '"Hipcam RealServer/V1.0"'
]

# ============================================================
# DORK ENGINE
# ============================================================
class DorkEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self.results = set()
        self.processed_urls = set()
        self.lock = asyncio.Lock()
        self.found_camera_urls = set()
        
    async def search_duckduckgo(self, dork, max_results=30):
        """DuckDuckGo Lite üzerinden dork araması"""
        urls = []
        try:
            search_url = "https://lite.duckduckgo.com/lite/"
            params = {'q': dork, 'kd': '-1'}
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            
            async with self.session.get(search_url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"])) as response:
                if response.status == 200:
                    html = await response.text()
                    pattern = r'<a[^>]+href="([^"]+)"[^>]*>'
                    links = re.findall(pattern, html)
                    
                    for link in links:
                        if link.startswith('/'):
                            link = 'https://duckduckgo.com' + link
                        if self.is_valid_url(link):
                            clean_url = self.clean_url(link)
                            if clean_url and clean_url not in self.processed_urls:
                                self.processed_urls.add(clean_url)
                                urls.append(clean_url)
                                # Terminalde göster
                                print(Fore.CYAN + f"🔍 Bulundu: {clean_url}")
                        if len(urls) >= max_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"DuckDuckGo hatası: {e}")
        
        return urls[:max_results]
    
    async def search_bing(self, dork, max_results=30):
        """Bing üzerinden dork araması"""
        urls = []
        try:
            search_url = "https://www.bing.com/search"
            params = {'q': dork, 'count': max_results, 'first': 1}
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            async with self.session.get(search_url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"])) as response:
                if response.status == 200:
                    html = await response.text()
                    pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?<h2'
                    links = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    
                    for link in links:
                        if self.is_valid_url(link):
                            clean_url = self.clean_url(link)
                            if clean_url and clean_url not in self.processed_urls:
                                self.processed_urls.add(clean_url)
                                urls.append(clean_url)
                                print(Fore.CYAN + f"🔍 Bulundu (Bing): {clean_url}")
                        if len(urls) >= max_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"Bing hatası: {e}")
        
        return urls[:max_results]
    
    async def search_startpage(self, dork, max_results=30):
        """Startpage üzerinden dork araması"""
        urls = []
        try:
            search_url = "https://www.startpage.com/sp/search"
            params = {'query': dork, 'num': max_results}
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            async with self.session.get(search_url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"])) as response:
                if response.status == 200:
                    html = await response.text()
                    pattern = r'<a[^>]+href="([^"]+)"[^>]*>'
                    links = re.findall(pattern, html)
                    
                    for link in links:
                        if 'startpage.com' in link:
                            continue
                        if self.is_valid_url(link):
                            clean_url = self.clean_url(link)
                            if clean_url and clean_url not in self.processed_urls:
                                self.processed_urls.add(clean_url)
                                urls.append(clean_url)
                                print(Fore.CYAN + f"🔍 Bulundu (Startpage): {clean_url}")
                        if len(urls) >= max_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"Startpage hatası: {e}")
        
        return urls[:max_results]
    
    def is_valid_url(self, url):
        """URL geçerlilik kontrolü"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return False
            if not parsed.netloc:
                return False
            ip_pattern = r'^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|169\.254\.|::1)'
            if re.match(ip_pattern, parsed.netloc):
                return False
            return True
        except:
            return False
    
    def clean_url(self, url):
        """URL'yi temizle ve normalize et"""
        try:
            parsed = urlparse(url)
            clean_path = parsed.path.rstrip('/')
            if not clean_path:
                clean_path = '/'
            return f"{parsed.scheme}://{parsed.netloc}{clean_path}"
        except:
            return url
    
    async def run_dork(self, dork, engine='duckduckgo'):
        """Belirtilen dork'u çalıştır"""
        results = []
        
        try:
            if engine == 'duckduckgo':
                results = await self.search_duckduckgo(dork, CONFIG["max_results_per_dork"])
            elif engine == 'bing':
                results = await self.search_bing(dork, CONFIG["max_results_per_dork"])
            elif engine == 'startpage':
                results = await self.search_startpage(dork, CONFIG["max_results_per_dork"])
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"Engine {engine} hatası: {e}")
        
        return results

# ============================================================
# URL FİLTRELEME
# ============================================================
class URLFilter:
    @staticmethod
    def is_camera_url(url):
        """URL'nin kamera ile ilgili olup olmadığını kontrol et"""
        camera_patterns = [
            r'camera', r'cam', r'webcam', r'ipcam', r'stream', r'live',
            r'mjpg', r'mjpeg', r'video', r'snapshot', r'view', r'axis',
            r'hikvision', r'dahua', r'foscam', r'vivotek', r'panasonic',
            r'sony', r'toshiba', r'netcam', r'acti', r'mobotix', r'dlink',
            r'viewer', r'guestimage', r'snapshot', r'liveapplet'
        ]
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in camera_patterns)

# ============================================================
# ASENKRON CANLILIK KONTROLÜ
# ============================================================
class AsyncHealthChecker:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(CONFIG["max_concurrent"])
        self.session = None
        self.ua = UserAgent()
        self.alive_urls = []
        self.dead_urls = []
        self.lock = asyncio.Lock()
        self.total_checked = 0
        
    async def check_url(self, url):
        """Tek bir URL'nin canlılığını kontrol et - TAM URL GÖSTERİMİ"""
        async with self.semaphore:
            for attempt in range(CONFIG["max_retries"]):
                try:
                    headers = {
                        'User-Agent': self.ua.random,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                        'Cache-Control': 'no-cache'
                    }
                    
                    timeout = aiohttp.ClientTimeout(total=CONFIG["timeout"])
                    
                    # TAM URL gösterimi
                    print(Fore.WHITE + f"🔄 Kontrol ediliyor: {url}")
                    
                    async with self.session.get(url, headers=headers, timeout=timeout,
                                              allow_redirects=True, ssl=False) as response:
                        status = response.status
                        
                        # Kamera tespiti
                        is_camera = False
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'image' in content_type or 'video' in content_type or 'mjpeg' in content_type:
                            is_camera = True
                        
                        # Başlıklardan kamera tespiti
                        headers_dict = dict(response.headers)
                        camera_headers = ['x-archive-camera', 'camera', 'webcam', 'axis', 'hikvision']
                        for header in camera_headers:
                            if any(header in k.lower() or header in v.lower() for k, v in headers_dict.items()):
                                is_camera = True
                                break
                        
                        # URL'den kamera tespiti
                        if URLFilter.is_camera_url(url):
                            is_camera = True
                        
                        if status == 200 and is_camera:
                            url_data = {
                                'url': url,
                                'status': status,
                                'content_type': content_type,
                                'timestamp': datetime.now().isoformat(),
                                'headers': dict(response.headers)
                            }
                            async with self.lock:
                                self.alive_urls.append(url_data)
                                self.total_checked += 1
                                global alive_urls_list
                                alive_urls_list.append(url_data)
                            
                            # YEŞİL - Canlı URL
                            print(Fore.GREEN + f"✅ CANLI: {url} | Status: {status} | Type: {content_type}")
                            return True
                        else:
                            # KIRMIZI - Kapalı veya kamera değil
                            if status != 200:
                                print(Fore.RED + f"❌ KAPALI: {url} | Status: {status}")
                            else:
                                print(Fore.YELLOW + f"⚠ KAMERA DEĞİL: {url} | Type: {content_type}")
                            return False
                            
                except asyncio.TimeoutError:
                    print(Fore.RED + f"⏱ ZAMAN AŞIMI: {url} (Deneme {attempt+1}/{CONFIG['max_retries']})")
                    if attempt == CONFIG["max_retries"] - 1:
                        async with self.lock:
                            self.dead_urls.append(url)
                            self.total_checked += 1
                        return False
                    await asyncio.sleep(1 * (attempt + 1))
                    
                except Exception as e:
                    print(Fore.RED + f"❌ HATA: {url} -> {str(e)} (Deneme {attempt+1}/{CONFIG['max_retries']})")
                    if attempt == CONFIG["max_retries"] - 1:
                        async with self.lock:
                            self.dead_urls.append(url)
                            self.total_checked += 1
                        return False
                    await asyncio.sleep(1 * (attempt + 1))
            
            return False
    
    async def check_multiple(self, urls):
        """Birden fazla URL'yi paralel kontrol et"""
        tasks = [self.check_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
    
    def get_statistics(self):
        """İstatistikleri döndür"""
        return {
            'alive': len(self.alive_urls),
            'dead': len(self.dead_urls),
            'total': self.total_checked
        }

# ============================================================
# ANA RECON BOT
# ============================================================
class FastDorkRecon:
    def __init__(self):
        global bot_instance
        bot_instance = self
        self.dork_engine = DorkEngine()
        self.health_checker = AsyncHealthChecker()
        self.all_urls = set()
        self.camera_urls = set()
        self.start_time = None
        self.end_time = None
        
    async def init_session(self):
        """Aiohttp session oluştur"""
        connector = aiohttp.TCPConnector(
            limit=CONFIG["max_concurrent"],
            limit_per_host=10,
            ttl_dns_cache=300,
            ssl=False
        )
        self.dork_engine.session = aiohttp.ClientSession(
            connector=connector,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        self.health_checker.session = aiohttp.ClientSession(
            connector=connector,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
    
    async def close_session(self):
        """Session'ları kapat"""
        if self.dork_engine.session:
            await self.dork_engine.session.close()
        if self.health_checker.session:
            await self.health_checker.session.close()
    
    async def run_dork_phase(self):
        """Dork arama fazı - TAM URL GÖSTERİMİ"""
        print(Fore.CYAN + "\n" + "="*70)
        print(Fore.CYAN + "  📡 DORK ARAMA FAZI BAŞLIYOR")
        print(Fore.CYAN + "="*70)
        print(Fore.WHITE + "🔍 Bulunan her URL terminalde gösterilecek...\n")
        
        all_dorks = GOOGLE_DORKS + SHODAN_STYLE_DORKS
        total_dorks = len(all_dorks)
        
        with tqdm(total=total_dorks, desc="Dork Tarama", unit="dork", ncols=100) as pbar:
            for i, dork in enumerate(all_dorks):
                if not running:
                    print(Fore.YELLOW + "⚠ İşlem durduruldu!")
                    break
                    
                try:
                    engines = ['duckduckgo', 'bing', 'startpage']
                    found_any = False
                    
                    for engine in engines:
                        results = await self.dork_engine.run_dork(dork, engine)
                        if results:
                            for url in results:
                                self.all_urls.add(url)
                                if URLFilter.is_camera_url(url):
                                    self.camera_urls.add(url)
                                    global found_camera_urls
                                    if url not in found_camera_urls:
                                        found_camera_urls.append(url)
                            
                            print(Fore.GREEN + f"✓ {dork[:40]}... -> {len(results)} URL ({engine})")
                            found_any = True
                            break
                        await asyncio.sleep(0.3)
                    
                    if not found_any:
                        print(Fore.YELLOW + f"⚠ {dork[:40]}... -> Sonuç yok")
                    
                    pbar.update(1)
                    await asyncio.sleep(CONFIG["request_delay"])
                    
                except Exception as e:
                    print(Fore.RED + f"✗ Dork hatası: {dork[:30]}... -> {e}")
                    pbar.update(1)
                    continue
        
        print(Fore.GREEN + f"\n✓ Toplam {len(self.all_urls)} benzersiz URL bulundu")
        print(Fore.GREEN + f"✓ {len(self.camera_urls)} potansiyel kamera URL'si tespit edildi")
    
    async def run_health_check_phase(self):
        """Canlılık kontrol fazı - TAM URL GÖSTERİMİ"""
        print(Fore.CYAN + "\n" + "="*70)
        print(Fore.CYAN + "  🔍 CANLILIK KONTROL FAZI BAŞLIYOR")
        print(Fore.CYAN + "="*70)
        print(Fore.WHITE + "📡 Her URL kontrol ediliyor, durumlar renkli olarak gösteriliyor...\n")
        
        if not self.camera_urls:
            print(Fore.YELLOW + "⚠ Hiç URL bulunamadı!")
            return
        
        url_list = list(self.camera_urls)[:1500]  # Limit
        print(Fore.WHITE + f"📊 {len(url_list)} URL kontrol ediliyor...\n")
        
        batch_size = 30
        for i in range(0, len(url_list), batch_size):
            if not running:
                print(Fore.YELLOW + "⚠ İşlem durduruldu, kaydediliyor...")
                break
                
            batch = url_list[i:i+batch_size]
            await self.health_checker.check_multiple(batch)
            
            # İstatistikleri göster
            stats = self.health_checker.get_statistics()
            print(Fore.CYAN + f"\n📊 İlerleme: Canlı: {stats['alive']} | Kapalı: {stats['dead']} | Toplam: {stats['total']}")
            print(Fore.CYAN + "-"*70 + "\n")
            
            # Ana dosyaya anlık yaz
            with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
                for url_data in self.health_checker.alive_urls:
                    if url_data not in alive_urls_list[-batch_size:]:
                        f.write(f"{url_data['url']} | Status: {url_data['status']} | Type: {url_data['content_type']} | Time: {url_data['timestamp']}\n")
            
            await asyncio.sleep(0.3)
        
        # Final istatistikler
        stats = self.health_checker.get_statistics()
        print(Fore.CYAN + "\n" + "="*70)
        print(Fore.GREEN + f"📊 TARAMA İSTATİSTİKLERİ")
        print(Fore.CYAN + "="*70)
        print(Fore.WHITE + f"Toplam URL: {stats['total']}")
        print(Fore.GREEN + f"Canlı URL: {stats['alive']}")
        print(Fore.RED + f"Kapalı URL: {stats['dead']}")
        if stats['total'] > 0:
            print(Fore.WHITE + f"Başarı Oranı: {(stats['alive']/stats['total'])*100:.2f}%")
    
    async def run(self):
        """Ana çalıştırma fonksiyonu"""
        self.start_time = datetime.now()
        
        print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🚀 FAST DORK RECON v2.0                                     ║
║     Otomatik Kamera Tarama Aracı - TAM URL GÖSTERİMİ           ║
║     Sadece Eğitim ve Savunma Testi Amaçlıdır                  ║
║     CTRL+C ile güvenli sonlandırma ve kaydetme                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print(Fore.YELLOW + "⚠ NOT: CTRL+C basarsanız tüm veriler otomatik kaydedilecek!\n")
        
        # Çıktı dosyasını temizle
        with open(CONFIG["output_file"], 'w', encoding='utf-8') as f:
            f.write(f"# Fast Dork Recon - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ===========================================\n\n")
        
        await self.init_session()
        
        try:
            # Faz 1: Dork araması
            await self.run_dork_phase()
            
            if not running:
                return
            
            # Faz 2: Canlılık kontrolü
            await self.run_health_check_phase()
            
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n⚠ Kullanıcı tarafından durduruldu! (Ctrl+C)")
        except Exception as e:
            print(Fore.RED + f"\n❌ Hata: {e}")
            if CONFIG["debug"]:
                import traceback
                traceback.print_exc()
        finally:
            await self.close_session()
            self.end_time = datetime.now()
            
            # Özet rapor
            duration = (self.end_time - self.start_time).total_seconds()
            stats = self.health_checker.get_statistics()
            
            print(Fore.CYAN + "\n" + "="*70)
            print(Fore.GREEN + "✅ TARAMA TAMAMLANDI")
            print(Fore.CYAN + "="*70)
            print(Fore.WHITE + f"⏱ Süre: {duration:.2f} saniye")
            print(Fore.GREEN + f"📁 Çıktı: {CONFIG['output_file']}")
            print(Fore.WHITE + f"📍 Toplam URL: {len(self.all_urls)}")
            print(Fore.GREEN + f"📷 Kamera URL: {len(self.camera_urls)}")
            print(Fore.GREEN + f"✅ Canlı URL: {stats['alive']}")
            print(Fore.RED + f"❌ Kapalı URL: {stats['dead']}")
            if stats['total'] > 0:
                print(Fore.WHITE + f"📊 Başarı: {(stats['alive']/stats['total'])*100:.2f}%")

# ============================================================
# ANA FONKSİYON
# ============================================================
async def main():
    global running
    try:
        bot = FastDorkRecon()
        await bot.run()
    except KeyboardInterrupt:
        running = False
        print(Fore.YELLOW + "\n⚠ Sonlandırılıyor... Veriler kaydediliyor...")
        # Signal handler zaten çalışacak
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⚠ Program sonlandırıldı. Veriler kaydedildi.")
        sys.exit(0)
