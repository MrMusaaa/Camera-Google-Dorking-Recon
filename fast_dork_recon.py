#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import re
import sys
import signal
from datetime import datetime
from urllib.parse import urlparse
from colorama import Fore, Style, init

init(autoreset=True)

# ============================================================
# KONFİG
# ============================================================
CONFIG = {
    "timeout": 8,
    "output_file": "canli_siteler.txt"
}

# ============================================================
# GLOBAL
# ============================================================
running = True
alive_urls_list = []
processed_urls = set()

# ============================================================
# SİNYAL YAKALAMA
# ============================================================
def signal_handler(sig, frame):
    global running, alive_urls_list
    print(Fore.YELLOW + "\n\n⚠ CTRL+C! Kaydediliyor...")
    running = False
    
    try:
        backup_file = f"canli_{datetime.now().strftime('%H%M%S')}.txt"
        with open(backup_file, 'w') as f:
            for url_data in alive_urls_list:
                f.write(f"{url_data['url']}\n")
        
        with open(CONFIG["output_file"], 'a') as f:
            for url_data in alive_urls_list:
                f.write(f"{url_data['url']}\n")
        
        print(Fore.GREEN + f"✅ Kaydedildi: {backup_file} ({len(alive_urls_list)} adet)")
        sys.exit(0)
    except:
        sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

# ============================================================
# ORJİNAL DORKLAR - AYNEN
# ============================================================
DORKS = [
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
# BASİT FİLTRE
# ============================================================
def is_bad_url(url):
    """Kötü URL'leri engelle"""
    url_lower = url.lower()
    
    bad = [
        '.org', 'github', 'youtube', 'outlook', 'facebook', 'twitter',
        'instagram', 'google', 'gmail', 'yahoo', 'hotmail',
        'wikipedia', 'stackoverflow', 'commentcamarche', 'forums',
        'blogger', 'wordpress', 'tiktok', 'live.com', 'microsoft'
    ]
    
    for b in bad:
        if b in url_lower:
            return True
    return False

# ============================================================
# ARAMA MOTORLARI - GOOGLE VE BING
# ============================================================
async def search_google(session, dork):
    """Google'da ara"""
    urls = []
    try:
        # Google düz arama URL'si
        search_url = "https://www.google.com/search"
        params = {'q': dork, 'num': 30}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        async with session.get(search_url, params=params, headers=headers,
                              timeout=aiohttp.ClientTimeout(total=8)) as response:
            if response.status == 200:
                html = await response.text()
                
                # Google link pattern
                pattern = r'<a[^>]+href="([^"]+)"[^>]*>'
                links = re.findall(pattern, html)
                
                for link in links:
                    if '/search' in link or 'google' in link:
                        continue
                    if link.startswith('/'):
                        continue
                    
                    clean = clean_url(link)
                    if not clean:
                        continue
                    
                    if not clean.startswith('http://'):
                        continue
                    
                    if is_bad_url(clean):
                        continue
                    
                    if clean in processed_urls:
                        continue
                    
                    processed_urls.add(clean)
                    urls.append(clean)
                    print(Fore.CYAN + f"🔍 (Google) {clean}")
    except:
        pass
    
    return urls

async def search_bing(session, dork):
    """Bing'de ara"""
    urls = []
    try:
        search_url = "https://www.bing.com/search"
        params = {'q': dork, 'count': 30}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        async with session.get(search_url, params=params, headers=headers,
                              timeout=aiohttp.ClientTimeout(total=8)) as response:
            if response.status == 200:
                html = await response.text()
                
                # Bing link pattern
                pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?<h2'
                links = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                
                for link in links:
                    if 'bing.com' in link:
                        continue
                    
                    clean = clean_url(link)
                    if not clean:
                        continue
                    
                    if not clean.startswith('http://'):
                        continue
                    
                    if is_bad_url(clean):
                        continue
                    
                    if clean in processed_urls:
                        continue
                    
                    processed_urls.add(clean)
                    urls.append(clean)
                    print(Fore.CYAN + f"🔍 (Bing) {clean}")
    except:
        pass
    
    return urls

async def search_duckduckgo(session, dork):
    """DuckDuckGo'da ara"""
    urls = []
    try:
        search_url = "https://lite.duckduckgo.com/lite/"
        params = {'q': dork, 'kd': '-1'}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        async with session.get(search_url, params=params, headers=headers,
                              timeout=aiohttp.ClientTimeout(total=8)) as response:
            if response.status == 200:
                html = await response.text()
                
                pattern = r'<a[^>]+href="([^"]+)"[^>]*>'
                links = re.findall(pattern, html)
                
                for link in links:
                    if link.startswith('/'):
                        continue
                    
                    clean = clean_url(link)
                    if not clean:
                        continue
                    
                    if not clean.startswith('http://'):
                        continue
                    
                    if is_bad_url(clean):
                        continue
                    
                    if clean in processed_urls:
                        continue
                    
                    processed_urls.add(clean)
                    urls.append(clean)
                    print(Fore.CYAN + f"🔍 (DDG) {clean}")
    except:
        pass
    
    return urls

def clean_url(url):
    """URL'yi temizle"""
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        path = parsed.path.rstrip('/')
        if not path:
            path = '/'
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    except:
        return None

# ============================================================
# CANLILIK KONTROLÜ
# ============================================================
async def check_url(session, url):
    """URL canlı mı kontrol et"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/*,*/*;q=0.8'
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5),
                              allow_redirects=True, ssl=False) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                
                is_cam = False
                if 'image' in content_type or 'video' in content_type or 'mjpeg' in content_type:
                    is_cam = True
                
                cam_keys = ['camera', 'cam', 'webcam', 'ipcam', 'stream', 'live', 'mjpg', 
                           'mjpeg', 'video', 'snapshot', 'view', 'axis', 'hikvision', 
                           'dahua', 'foscam', 'vivotek', 'dlink', 'cgi-bin', 'camctrl']
                if any(k in url.lower() for k in cam_keys):
                    is_cam = True
                
                if is_cam:
                    print(Fore.GREEN + f"✅ {url}")
                    return {'url': url, 'status': 200, 'content_type': content_type}
                else:
                    print(Fore.YELLOW + f"⚠ {url}")
                    return None
            else:
                print(Fore.RED + f"❌ {url} ({response.status})")
                return None
    except:
        print(Fore.RED + f"❌ {url}")
        return None

# ============================================================
# ANA FONKSİYON - ÇOKLU ARAMA
# ============================================================
async def main():
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🚀 FAST DORK RECON v14.0 - ÇOKLU ARAMA                   ║
║     Google + Bing + DuckDuckGo AYNI ANDA                    ║
║     BASİT - SADECE .org ENGEL                               ║
║     CTRL+C ile kaydet                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print(Fore.YELLOW + f"⚠ {len(DORKS)} dork, 3 motor AYNI ANDA taranacak\n")
    
    with open(CONFIG["output_file"], 'w') as f:
        f.write(f"# Kamera URL'leri - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    all_camera_urls = []
    
    async with aiohttp.ClientSession() as session:
        for i, dork in enumerate(DORKS, 1):
            if not running:
                break
            
            print(Fore.WHITE + f"\n[{i}/{len(DORKS)}] {dork[:50]}...")
            print(Fore.WHITE + "-" * 50)
            
            # 3 motoru AYNI ANDA çalıştır
            tasks = [
                search_google(session, dork),
                search_bing(session, dork),
                search_duckduckgo(session, dork)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Tüm sonuçları birleştir
            total = 0
            for urls in results:
                all_camera_urls.extend(urls)
                total += len(urls)
            
            if total > 0:
                print(Fore.GREEN + f"✓ Toplam {total} URL bulundu")
            else:
                print(Fore.YELLOW + "⚠ Sonuç yok")
            
            await asyncio.sleep(0.5)
    
    # Benzersiz yap
    all_camera_urls = list(set(all_camera_urls))
    
    print(Fore.CYAN + f"\n{'='*60}")
    print(Fore.GREEN + f"📊 Toplam {len(all_camera_urls)} benzersiz URL bulundu")
    
    if all_camera_urls:
        print(Fore.CYAN + "\n🔍 CANLILIK KONTROLÜ...\n")
        
        alive = []
        batch_size = 20
        
        for i in range(0, len(all_camera_urls), batch_size):
            if not running:
                break
            
            batch = all_camera_urls[i:i+batch_size]
            tasks = [check_url(session, url) for url in batch]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result:
                    alive.append(result)
                    alive_urls_list.append(result)
                    
                    with open(CONFIG["output_file"], 'a') as f:
                        f.write(f"{result['url']}\n")
            
            print(Fore.CYAN + f"\n📊 Canlı: {len(alive)} | Kontrol: {i+len(batch)}")
            await asyncio.sleep(0.2)
        
        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.GREEN + f"✅ TAMAM! Canlı kamera: {len(alive)}")
        print(Fore.GREEN + f"📁 {CONFIG['output_file']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n⚠ Bitti.")
        sys.exit(0)
