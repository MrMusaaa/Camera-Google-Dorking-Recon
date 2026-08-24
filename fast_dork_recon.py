#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import re
import os
import sys
import time
import signal
from datetime import datetime
from urllib.parse import urlparse, quote
from colorama import Fore, Style, init
from fake_useragent import UserAgent
from tqdm import tqdm
import random

init(autoreset=True)

# ============================================================
# KONFİGÜRASYON
# ============================================================
CONFIG = {
    "max_concurrent": 50,
    "timeout": 5,
    "max_retries": 2,
    "output_file": "canli_siteler.txt",
    "debug": False,
    "max_results_per_dork": 30,
    "max_pages_per_dork": 5,
    "request_delay": 0.3
}

# ============================================================
# GLOBAL
# ============================================================
running = True
bot_instance = None
alive_urls_list = []
found_camera_urls = set()
backup_counter = 0
backup_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

# ============================================================
# SİNYAL YAKALAMA
# ============================================================
def signal_handler(sig, frame):
    global running, alive_urls_list, backup_counter
    print(Fore.YELLOW + "\n\n⚠ CTRL+C tespit edildi! Veriler kaydediliyor...")
    running = False
    
    try:
        letter = backup_letters[backup_counter % len(backup_letters)]
        backup_counter += 1
        backup_file = f"canli_{letter}.txt"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"# Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ===========================================\n\n")
            for url_data in alive_urls_list:
                f.write(f"{url_data['url']} | Status: {url_data['status']} | Type: {url_data['content_type']} | Time: {url_data['timestamp']}\n")
        
        with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
            for url_data in alive_urls_list:
                f.write(f"{url_data['url']} | Status: {url_data['status']} | Type: {url_data['content_type']} | Time: {url_data['timestamp']}\n")
        
        print(Fore.GREEN + f"\n✅ Kaydedildi: {backup_file}")
        print(Fore.GREEN + f"📊 Toplam: {len(alive_urls_list)}")
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"❌ Hata: {e}")
        sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

# ============================================================
# ORJİNAL DORKLAR - HİÇ DOKUNMA
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
# KAMERA FİLTRELEME - DAHA AZ FİLTRE
# ============================================================
class CameraFilter:
    @staticmethod
    def is_camera_url(url):
        camera_patterns = [
            r'camera', r'cam', r'webcam', r'ipcam', r'stream', r'live',
            r'mjpg', r'mjpeg', r'video', r'snapshot', r'view', r'axis',
            r'hikvision', r'dahua', r'foscam', r'vivotek', r'panasonic',
            r'sony', r'toshiba', r'netcam', r'acti', r'mobotix', r'dlink',
            r'viewer', r'guestimage', r'liveapplet', r'index\.shtml',
            r'view\.shtml', r'frame\.shtml', r'main\.cgi', r'cgi-bin',
            r'camctrl', r'currentpic', r'video\.cgi', r'image\.jpg',
            r'live\.htm', r'cam\.html', r'dvr', r'cctv', r'surveillance',
            r'control', r'snapshot', r'cgi'
        ]
        return any(re.search(p, url.lower()) for p in camera_patterns)
    
    @staticmethod
    def is_http_only(url):
        if not url.startswith('http://'):
            return False
        
        # SADECE EN ÖNEMLİ ENGELLEMELER
        blocked = [
            'github', 'youtube', 'outlook', 'facebook', 'twitter',
            'instagram', 'google', 'gmail', 'yahoo', 'hotmail',
            'wikipedia', 'stackoverflow', 'commentcamarche', 'forums'
        ]
        
        url_lower = url.lower()
        for b in blocked:
            if b in url_lower:
                return False
        
        parsed = urlparse(url)
        ip_pattern = r'^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|169\.254\.)'
        if re.match(ip_pattern, parsed.netloc):
            return False
        
        return True

# ============================================================
# DORK ENGINE - EK ARAMA MOTORLARI
# ============================================================
class DorkEngine:
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self.processed_urls = set()
        
    async def search_with_pagination(self, dork, max_pages=5, per_page=30):
        all_urls = []
        
        for page in range(1, max_pages + 1):
            if not running:
                break
                
            start = (page - 1) * per_page
            
            # ÖNCE DUCKDUCKGO
            urls = await self.search_duckduckgo(dork, per_page, start)
            
            # SONRA BING
            if not urls:
                urls = await self.search_bing(dork, per_page)
            
            # SONRA STARTPAGE
            if not urls:
                urls = await self.search_startpage(dork, per_page)
            
            if not urls:
                if page == 1:
                    break
                if len(all_urls) == 0:
                    break
            
            all_urls.extend(urls)
            
            if len(urls) < per_page:
                break
                
            await asyncio.sleep(0.3)
        
        return all_urls
    
    async def search_duckduckgo(self, dork, num_results=30, start=0):
        urls = []
        try:
            search_url = "https://lite.duckduckgo.com/lite/"
            params = {'q': dork, 'kd': '-1', 's': start}
            
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
                        if link.startswith('/'):
                            link = 'https://duckduckgo.com' + link
                        
                        clean_url = self.clean_url(link)
                        if clean_url:
                            if CameraFilter.is_http_only(clean_url) and CameraFilter.is_camera_url(clean_url):
                                if clean_url not in self.processed_urls:
                                    self.processed_urls.add(clean_url)
                                    urls.append(clean_url)
                                    print(Fore.CYAN + f"🔍 {clean_url}")
                        
                        if len(urls) >= num_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"DDG Hata: {e}")
        
        return urls
    
    async def search_bing(self, dork, num_results=30):
        urls = []
        try:
            search_url = "https://www.bing.com/search"
            params = {'q': dork, 'count': num_results}
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            async with self.session.get(search_url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=CONFIG["timeout"])) as response:
                if response.status == 200:
                    html = await response.text()
                    pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?<h2'
                    links = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                    
                    for link in links:
                        clean_url = self.clean_url(link)
                        if clean_url:
                            if CameraFilter.is_http_only(clean_url) and CameraFilter.is_camera_url(clean_url):
                                if clean_url not in self.processed_urls:
                                    self.processed_urls.add(clean_url)
                                    urls.append(clean_url)
                                    print(Fore.CYAN + f"🔍 (Bing) {clean_url}")
                        if len(urls) >= num_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"Bing Hata: {e}")
        
        return urls
    
    async def search_startpage(self, dork, num_results=30):
        urls = []
        try:
            search_url = "https://www.startpage.com/sp/search"
            params = {'query': dork, 'num': num_results}
            
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
                        clean_url = self.clean_url(link)
                        if clean_url:
                            if CameraFilter.is_http_only(clean_url) and CameraFilter.is_camera_url(clean_url):
                                if clean_url not in self.processed_urls:
                                    self.processed_urls.add(clean_url)
                                    urls.append(clean_url)
                                    print(Fore.CYAN + f"🔍 (SP) {clean_url}")
                        if len(urls) >= num_results:
                            break
                            
        except Exception as e:
            if CONFIG["debug"]:
                print(Fore.RED + f"Startpage Hata: {e}")
        
        return urls
    
    def clean_url(self, url):
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                return None
            if not parsed.netloc:
                return None
            clean_path = parsed.path.rstrip('/')
            if not clean_path:
                clean_path = '/'
            return f"{parsed.scheme}://{parsed.netloc}{clean_path}"
        except:
            return None

# ============================================================
# HIZLI HEALTH CHECK
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
        if not url.startswith('http://'):
            return False
        
        async with self.semaphore:
            try:
                headers = {
                    'User-Agent': self.ua.random,
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Connection': 'keep-alive'
                }
                
                timeout = aiohttp.ClientTimeout(total=5)
                
                async with self.session.get(url, headers=headers, timeout=timeout,
                                          allow_redirects=True, ssl=False) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')
                    
                    is_camera = False
                    if 'image' in content_type or 'video' in content_type or 'mjpeg' in content_type:
                        is_camera = True
                    if CameraFilter.is_camera_url(url):
                        is_camera = True
                    
                    if status == 200 and is_camera:
                        url_data = {
                            'url': url,
                            'status': status,
                            'content_type': content_type,
                            'timestamp': datetime.now().isoformat()
                        }
                        async with self.lock:
                            self.alive_urls.append(url_data)
                            self.total_checked += 1
                            global alive_urls_list
                            alive_urls_list.append(url_data)
                        
                        print(Fore.GREEN + f"✅ {url}")
                        
                        with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
                            f.write(f"{url} | Status: {status} | Type: {content_type} | Time: {datetime.now().isoformat()}\n")
                        
                        return True
                    else:
                        if status != 200:
                            print(Fore.RED + f"❌ {url}")
                        return False
                        
            except Exception as e:
                return False
    
    async def check_multiple(self, urls):
        tasks = [self.check_url(url) for url in urls]
        await asyncio.gather(*tasks)
    
    def get_statistics(self):
        return {
            'alive': len(self.alive_urls),
            'dead': len(self.dead_urls),
            'total': self.total_checked
        }

# ============================================================
# ANA BOT
# ============================================================
class FastDorkRecon:
    def __init__(self):
        global bot_instance
        bot_instance = self
        self.dork_engine = DorkEngine()
        self.health_checker = AsyncHealthChecker()
        self.camera_urls = set()
        self.start_time = None
        
    async def init_session(self):
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
        if self.dork_engine.session:
            await self.dork_engine.session.close()
        if self.health_checker.session:
            await self.health_checker.session.close()
    
    async def run(self):
        self.start_time = datetime.now()
        
        print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🚀 FAST DORK RECON v12.0                                   ║
║     ORJİNAL DORKLAR - EK ARAMA MOTORLARI                      ║
║     DAHA AZ FİLTRE - DAHA FAZLA SONUÇ                        ║
║     DuckDuckGo + Bing + Startpage                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print(Fore.YELLOW + f"⚠ {len(GOOGLE_DORKS)} dork, {CONFIG['max_pages_per_dork']} sayfa, 3 motor\n")
        
        with open(CONFIG["output_file"], 'w', encoding='utf-8') as f:
            f.write(f"# HTTP Kamera - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ===========================================\n\n")
        
        await self.init_session()
        
        try:
            print(Fore.CYAN + "="*60)
            print(Fore.CYAN + "  📡 TARAMA BAŞLADI")
            print(Fore.CYAN + "="*60 + "\n")
            
            with tqdm(total=len(GOOGLE_DORKS), desc="Dork", unit="", ncols=80) as pbar:
                for dork in GOOGLE_DORKS:
                    if not running:
                        break
                    
                    try:
                        results = await self.dork_engine.search_with_pagination(
                            dork, 
                            CONFIG["max_pages_per_dork"], 
                            CONFIG["max_results_per_dork"]
                        )
                        
                        if results:
                            for url in results:
                                self.camera_urls.add(url)
                            print(Fore.GREEN + f"✓ {dork[:30]}... -> {len(results)}")
                        else:
                            print(Fore.YELLOW + f"⚠ {dork[:30]}...")
                        
                        pbar.update(1)
                        await asyncio.sleep(CONFIG["request_delay"])
                        
                    except Exception as e:
                        print(Fore.RED + f"✗ {dork[:20]}...")
                        pbar.update(1)
                        continue
            
            print(Fore.GREEN + f"\n✓ Bulunan: {len(self.camera_urls)}")
            
            if self.camera_urls:
                print(Fore.CYAN + "\n" + "="*60)
                print(Fore.CYAN + "  🔍 CANLILIK KONTROLÜ")
                print(Fore.CYAN + "="*60 + "\n")
                
                url_list = list(self.camera_urls)[:500]
                batch_size = 25
                
                for i in range(0, len(url_list), batch_size):
                    if not running:
                        break
                    
                    batch = url_list[i:i+batch_size]
                    await self.health_checker.check_multiple(batch)
                    
                    stats = self.health_checker.get_statistics()
                    print(Fore.CYAN + f"\n📊 Canlı: {stats['alive']} | Kapalı: {stats['dead']}")
                    print(Fore.CYAN + "-"*40)
                    
                    await asyncio.sleep(0.2)
            
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n⚠ Durduruldu!")
        except Exception as e:
            print(Fore.RED + f"\n❌ {e}")
        finally:
            await self.close_session()
            stats = self.health_checker.get_statistics()
            
            print(Fore.CYAN + "\n" + "="*60)
            print(Fore.GREEN + "✅ TAMAM")
            print(Fore.CYAN + "="*60)
            print(Fore.GREEN + f"📁 {CONFIG['output_file']}")
            print(Fore.WHITE + f"📍 Bulunan: {len(self.camera_urls)}")
            print(Fore.GREEN + f"✅ Canlı: {stats['alive']}")

async def main():
    bot = FastDorkRecon()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⚠ Bitti.")
        sys.exit(0)
