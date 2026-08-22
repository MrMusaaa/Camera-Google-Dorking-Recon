#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import re
import json
import os
import sys
import time
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
    "log_file": "recon_log.txt",
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ],
    "request_delay": 1.0,
    "use_proxy": False,
    "proxy_list": [],
    "max_results_per_dork": 50,
    "debug": False
}

# ============================================================
# DORK LİSTESİ - Google Dorks
# ============================================================
GOOGLE_DORKS = [
    'inurl:"CgiStart?page="',
    'inurl:camctrl.cgi',
    'inurl:"view/index.shtml"',
    'intitle:"IP CAMERA Viewer" intext:"setting | Client setting"',
    'intitle:"Device(" AND intext:"Network Camera" AND "language:" "AND "Password"',
    'intitle:"webcam 7" inurl:"/gallery.html"',
    'intitle:"yawcam" inurl:":8081"',
    'intitle:"iGuard Fingerprint Security System"',
    '(intitle:MOBOTIX intitle:PDAS) | (intitle:MOBOTIX intitle:Seiten) | (inurl:/pda/index.html +camera)',
    'intitle:"Edr1680 remote viewer"',
    'intitle:"NetCam Live Image" -.edu -.gov -johnny.ihackstuff.com',
    'intitle:"INTELLINET" intitle:"IP Camera Homepage"',
    'intitle:"WEBDVR" -inurl:product -inurl:demo',
    'intitle:"Middle frame of Videoconference Management System" ext:htm',
    'tilt intitle:"Live View / - AXIS" | inurl:view/view.shtml',
    'intitle:"AXIS 240 Camera Server" intext:"server push" -help',
    'intitle:"--- VIDEO WEB SERVER ---" intext:"Video Web Server" "Any time & Any where" username password',
    'intitle:HomeSeer.Web.Control | Home.Status.Events.Log',
    'intitle:"supervisioncam protocol"',
    'intitle:"active webcam page"',
    'inurl:"MultiCameraFrame?Mode=Motion"',
    'VB Viewer inurl:/viewer/live/ja/live.html',
    'inurl:control/camerainfo',
    'intitle:"webcamXP 5" -download',
    'inurl:"/view/view.shtml?id="',
    'inurl:/view/viewer_index.shtml',
    'intext:"powered by webcamXP 5"',
    'intitle:"webcam 7" inurl:"8080" -intext:"8080"',
    'intitle:"Live View /- AXIS" |inurl:view/view.shtml OR inurl:view/indexFrame.shtml |intitle:"MJPG Live Demo" |intext:"Select preset position"',
    'allintitle:Axis 2.10 OR 2.12 OR 2.30 OR 2.31 OR 2.32 OR 2.33 OR 2.34 OR 2.40 OR 2.42 OR 2.43 "Network Camera"',
    'allintitle:Edr1680 remote viewer',
    'allintitle:EverFocus |EDSR |EDSR400 Applet',
    'allintitle:EDR1600 login |Welcome',
    'intitle:"BlueNet Video Viewer"',
    'intitle:"SNC-RZ30" -demo',
    'inurl:cgi-bin/guestimage.html',
    '(intitle:(EyeSpyFX|OptiCamFX) "go to camera")|(inurl:servlet/DetectBrowser)',
    'intitle:"Veo Observer XT"',
    'inurl:shtml|pl|php|htm|asp|aspx|pDf|cfm -(intext:observer)',
    'inurl:top.htm inurl:currenttime',
    'intitle:"webcamXP 5"',
    'inurl:"lvappl.htm"',
    'inurl:/view.shtml',
    'intitle:"Live View/ — AXIS"',
    'inurl:iview/view.shtml',
    'inurl:ViewerFrame?M0de=',
    'inurl:ViewerFrame?M0de=Refresh',
    'inurl:axis-cgi/jpg',
    'inurl:axis-cgi/mjpg',
    'inurl:view/indexFrame.shtml',
    'inurl:view/index.shtml',
    'inurl:view/view.shtml',
    'liveapplet',
    'intitle:"live view" intitle:axis',
    'intitle:liveapplet',
    'allintitle:"Network Camera NetworkCamera"',
    'intitle:axis intitle:"video server"',
    'intitle:liveapplet inurl:LvAppl',
    'intitle:"EvoCam" inurl:"webcam.html"',
    'intitle:"Live NetSnap Cam-Server feed"',
    'intitle:"Live View/ — AX|S"',
    'intitle:"Live View/ — AXIS 206M"',
    'intitle:"Live View/ — AXIS 210"',
    'inurl:indexFrame.shtml Axis',
    'inurl:"MultiCameraFrame?Mode=Motion"',
    'intitle:start inurl:cgistart',
    'intitle:"WJ-NTI 04 Main Page"',
    'intitle:snc-220 inurl:home/',
    'intitle:snc-cs3 inurl:home/',
    'intitle:snc-r230 inurl:home/',
    'intitle:"sony network camera snc-pl"',
    'intitle:"sony network camera snc-ml"',
    'site:.viewnetcam.com -www.viewnetcam.com',
    'intitle:"Toshiba Network Camera" user login',
    'intitle:"netcam live image"',
    'intitle:"i-Catcher Console - Web Monitor"',
    'intitle:"IP Webcam" inurl:"/greet.html"',
    'AXIS Camera exploit',
    'intitle:"NetCamSC*"',
    'intitle:"NetCamXL*"',
    'inurl:"view.shtml" "camera"',
    'intitle:"NetCamSC*" | intitle:"NetCamXL*" inurl:index.html',
    'inurl:"live/cam.html"',
    'inurl:"view.shtml" "Network Camera"',
    'inurl:/config/cam_portal.cgi "Panasonic"',
    '"Camera Live Image" inurl:"guestimage.html"',
    'intitle:"webcam" inurl:login',
    'inurl:/ViewerFrame? intitle:"Network Camera NetworkCamera"',
    'intitle:"WEBCAM 7 " -inurl:/admin.html',
    'intitle:NetworkCamera intext:"Pan / Tilt" inurl:ViewerFrame',
    'inurl:/live.htm intext:"M-JPEG"|"System Log"|"Camera-1"|"View Control"',
    'intitle:"webcamXP 5" inurl:8080 "Live"',
    'inurl:"MultiCameraFrame?Mode=Motion"',
    'intitle:"IP CAMERA Viewer" intext:"setting | Client setting"',
    'intitle:"Weather Wing WS-2"'
]

# ============================================================
# SHODAN BENZERİ DORKLAR (HTTP Header/Fingerprint tabanlı)
# ============================================================
SHODAN_STYLE_DORKS = [
    'product:"Hikvision IP Camera"',
    'http.title:"WEB VIEW"',
    'http.component:"mootools" -401',
    'Server: SQ-WEBCAM',
    'Server: yawcam',
    'Server: uc-httpd',
    'title:camera',
    'title:"Webcam"',
    'has_screenshot:true',
    '"Hipcam RealServer/V1.0"',
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
    'product:"Loxone Intercom"',
    'product:"Comelit Camera"',
    'product:"Canon VB Camera"',
    'product:"WVC210 Wireless-G PTZ"',
    'product:"SNC-RZ30"',
    'product:"iGuard Fingerprint"',
    'product:"Veo Observer"',
    'product:"BlueNet Video"',
    'product:"NetCamXL"',
    'product:"NetCamSC"',
    'product:"AirLink Camera"',
    'product:"Inspire DVR"',
    'product:"Milestone Portal"',
    'product:"MotionEYE"',
    'product:"Defeway Camera"',
    'product:"ExecqVision"',
    'product:"Digital Watching NVR"',
    'product:"NL NUUO"',
    'product:"Security Spy"',
    'product:"Webcam 7"',
    'product:"webcamXP"'
]

# ============================================================
# DORK ENGINE - Google ve DuckDuckGo üzerinden arama
# ============================================================
class DorkEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self.results = set()
        self.processed_urls = set()
        self.lock = asyncio.Lock()
        
    async def search_duckduckgo(self, dork, max_results=50):
        """DuckDuckGo Lite üzerinden dork araması"""
        urls = []
        try:
            # DuckDuckGo Lite API
            search_url = "https://lite.duckduckgo.com/lite/"
            params = {
                'q': dork,
                'kd': '-1'  # Tüm bölgeler
            }
            
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
                    # Linkleri ayıkla
                    pattern = r'<a[^>]+href="([^"]+)"[^>]*>'
                    links = re.findall(pattern, html)
                    
                    for link in links:
                        if link.startswith('/'):
                            link = 'https://duckduckgo.com' + link
                        if self.is_valid_url(link):
                            urls.append(link)
                        if len(urls) >= max_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"DuckDuckGo hatası: {e}")
        
        return urls[:max_results]
    
    async def search_bing(self, dork, max_results=50):
        """Bing üzerinden dork araması (alternatif)"""
        urls = []
        try:
            search_url = "https://www.bing.com/search"
            params = {
                'q': dork,
                'count': max_results,
                'first': 1
            }
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            async with self.session.get(search_url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"])) as response:
                if response.status == 200:
                    html = await response.text()
                    # Bing link pattern
                    pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?<h2'
                    links = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    
                    for link in links:
                        if self.is_valid_url(link):
                            urls.append(link)
                        if len(urls) >= max_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"Bing hatası: {e}")
        
        return urls[:max_results]
    
    async def search_startpage(self, dork, max_results=50):
        """Startpage üzerinden dork araması (özel)"""
        urls = []
        try:
            search_url = "https://www.startpage.com/sp/search"
            params = {
                'query': dork,
                'num': max_results
            }
            
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
                            urls.append(link)
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
            # Yerel IP'leri ve özel aralıkları filtrele
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
            # Sorgu parametrelerini temizle
            clean_path = parsed.path.rstrip('/')
            if not clean_path:
                clean_path = '/'
            return f"{parsed.scheme}://{parsed.netloc}{clean_path}"
        except:
            return url
    
    async def run_dork(self, dork, engine='duckduckgo'):
        """Belirtilen dork'u çalıştır"""
        results = []
        
        if engine == 'duckduckgo':
            results = await self.search_duckduckgo(dork, CONFIG["max_results_per_dork"])
        elif engine == 'bing':
            results = await self.search_bing(dork, CONFIG["max_results_per_dork"])
        elif engine == 'startpage':
            results = await self.search_startpage(dork, CONFIG["max_results_per_dork"])
        
        # URL'leri temizle ve normalize et
        cleaned = []
        for url in results:
            clean = self.clean_url(url)
            if clean and clean not in self.processed_urls:
                self.processed_urls.add(clean)
                cleaned.append(clean)
        
        return cleaned

# ============================================================
# URL FİLTRELEME VE İŞLEME
# ============================================================
class URLFilter:
    @staticmethod
    def is_camera_url(url):
        """URL'nin kamera ile ilgili olup olmadığını kontrol et"""
        camera_patterns = [
            r'camera', r'cam', r'webcam', r'ipcam', r'stream', r'live',
            r'mjpg', r'mjpeg', r'video', r'snapshot', r'view', r'axis',
            r'hikvision', r'dahua', r'foscam', r'vivotek', r'panasonic',
            r'sony', r'toshiba', r'netcam', r'acti', r'mobotix', r'dlink'
        ]
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in camera_patterns)
    
    @staticmethod
    def extract_ips(text):
        """Metinden IP adreslerini çıkar"""
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, text)
        valid_ips = []
        for ip in ips:
            parts = ip.split('.')
            if all(0 <= int(p) <= 255 for p in parts):
                valid_ips.append(ip)
        return valid_ips
    
    @staticmethod
    def extract_domains(text):
        """Metinden alan adlarını çıkar"""
        domain_pattern = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
        return re.findall(domain_pattern, text)

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
        
    async def check_url(self, url):
        """Tek bir URL'nin canlılığını kontrol et"""
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
                            async with self.lock:
                                self.alive_urls.append({
                                    'url': url,
                                    'status': status,
                                    'content_type': content_type,
                                    'timestamp': datetime.now().isoformat(),
                                    'headers': dict(response.headers)
                                })
                            return True
                        else:
                            return False
                            
                except asyncio.TimeoutError:
                    if attempt == CONFIG["max_retries"] - 1:
                        async with self.lock:
                            self.dead_urls.append(url)
                        return False
                    await asyncio.sleep(1 * (attempt + 1))
                    
                except Exception as e:
                    if CONFIG["debug"]:
                        print(Fore.RED + f"Hata {url}: {e}")
                    if attempt == CONFIG["max_retries"] - 1:
                        async with self.lock:
                            self.dead_urls.append(url)
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
            'total': len(self.alive_urls) + len(self.dead_urls)
        }

# ============================================================
# ANA RECON BOT
# ============================================================
class FastDorkRecon:
    def __init__(self):
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
        """Dork arama fazı"""
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + "  📡 DORK ARAMA FAZI BAŞLIYOR")
        print(Fore.CYAN + "="*60)
        
        all_dorks = GOOGLE_DORKS + SHODAN_STYLE_DORKS
        total_dorks = len(all_dorks)
        
        with tqdm(total=total_dorks, desc="Dork Tarama", unit="dork") as pbar:
            for i, dork in enumerate(all_dorks):
                try:
                    # Farklı motorları dene
                    engines = ['duckduckgo', 'bing', 'startpage']
                    for engine in engines:
                        results = await self.dork_engine.run_dork(dork, engine)
                        if results:
                            self.all_urls.update(results)
                            print(Fore.GREEN + f"✓ {dork[:50]}... -> {len(results)} URL bulundu ({engine})")
                            break
                        await asyncio.sleep(0.5)
                    
                    # Kamera URL'lerini filtrele
                    for url in results:
                        if URLFilter.is_camera_url(url):
                            self.camera_urls.add(url)
                    
                    pbar.update(1)
                    
                    # Rate limiting
                    await asyncio.sleep(CONFIG["request_delay"])
                    
                except Exception as e:
                    print(Fore.RED + f"✗ Dork hatası: {dork[:30]}... -> {e}")
                    pbar.update(1)
                    continue
        
        print(Fore.GREEN + f"\n✓ Toplam {len(self.all_urls)} benzersiz URL bulundu")
        print(Fore.GREEN + f"✓ {len(self.camera_urls)} potansiyel kamera URL'si tespit edildi")
    
    async def run_health_check_phase(self):
        """Canlılık kontrol fazı"""
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + "  🔍 CANLILIK KONTROL FAZI BAŞLIYOR")
        print(Fore.CYAN + "="*60)
        
        if not self.camera_urls:
            print(Fore.YELLOW + "⚠ Hiç URL bulunamadı!")
            return
        
        url_list = list(self.camera_urls)[:1000]  # Limit
        print(Fore.WHITE + f"📊 {len(url_list)} URL kontrol ediliyor...")
        
        batch_size = 50
        for i in range(0, len(url_list), batch_size):
            batch = url_list[i:i+batch_size]
            await self.health_checker.check_multiple(batch)
            
            # Anlık geri bildirim
            alive = self.health_checker.alive_urls
            dead = self.health_checker.dead_urls
            
            print(Fore.GREEN + f"✓ Canlı: {len(alive)} | " + Fore.RED + f"✗ Kapalı: {len(dead)}")
            
            # canli_siteler.txt'ye yaz
            with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
                for url_data in alive[-batch_size:]:
                    f.write(f"{url_data['url']} | Status: {url_data['status']} | Type: {url_data['content_type']} | Time: {url_data['timestamp']}\n")
            
            # Terminale yaz
            for url_data in alive[-batch_size:]:
                print(Fore.GREEN + f"  ✅ {url_data['url']}")
            
            await asyncio.sleep(0.5)
        
        # İstatistikler
        stats = self.health_checker.get_statistics()
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.GREEN + f"📊 TARAMA İSTATİSTİKLERİ")
        print(Fore.CYAN + "="*60)
        print(Fore.WHITE + f"Toplam URL: {stats['total']}")
        print(Fore.GREEN + f"Canlı URL: {stats['alive']}")
        print(Fore.RED + f"Kapalı URL: {stats['dead']}")
        print(Fore.WHITE + f"Başarı Oranı: {stats['alive']/(stats['total'])*100:.2f}%")
    
    async def run(self):
        """Ana çalıştırma fonksiyonu"""
        self.start_time = datetime.now()
        
        print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 FAST DORK RECON v2.0                                 ║
║     Otomatik Kamera Tarama Aracı                            ║
║     Sadece Eğitim ve Savunma Testi Amaçlıdır              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Çıktı dosyasını temizle
        with open(CONFIG["output_file"], 'w', encoding='utf-8') as f:
            f.write(f"# Fast Dork Recon - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ===========================================\n\n")
        
        await self.init_session()
        
        try:
            # Faz 1: Dork araması
            await self.run_dork_phase()
            
            # Faz 2: Canlılık kontrolü
            await self.run_health_check_phase()
            
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n⚠ Kullanıcı tarafından durduruldu!")
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
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.GREEN + "✅ TARAMA TAMAMLANDI")
            print(Fore.CYAN + "="*60)
            print(Fore.WHITE + f"⏱ Süre: {duration:.2f} saniye")
            print(Fore.GREEN + f"📁 Çıktı: {CONFIG['output_file']}")
            print(Fore.WHITE + f"📍 Toplam URL: {len(self.all_urls)}")
            print(Fore.GREEN + f"📷 Kamera URL: {len(self.camera_urls)}")
            print(Fore.GREEN + f"✅ Canlı URL: {len(self.health_checker.alive_urls)}")
            print(Fore.RED + f"❌ Kapalı URL: {len(self.health_checker.dead_urls)}")

# ============================================================
# ANA FONKSİYON
# ============================================================
async def main():
    bot = FastDorkRecon()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
