#! /usr/bin/env python3
# Copyright (c) 2020 Snoop Project <snoopproject@protonmail.com> 
"Network self-test"

import speedtest  # type: ignore
from rich.console import Console
from rich.panel import Panel
from rich.style import Style as STL


def nettest():
    console2 = Console()
    with console2.status("[cyan] Please wait, running network self-test...", spinner='noise'):
        servers = []
        try:
            s = speedtest.Speedtest(secure=True)
            s.get_servers(servers)
            s.get_best_server()
            s.download(threads=None)
            s.upload(threads=None)

            a = s.results.dict()

            d = round(a.get("download") / 1_000_000, 2)
            u = round(a.get("upload") / 1_000_000, 2)
            p = round(a.get("ping"))
            c = a.get("client")

# Download speed.
            try:
                if d < 3: d = f"Download: [bold red]{d}[/bold red] Mbps"
                elif 3 <= d <= 5.5: d = f"Download: [yellow]{d}[/yellow] Mbps"
                elif d > 5.5: d = f"Download: [bold green]{d}[/bold green] Mbps"
            except:
                d = f"Download: [bold red]Failure[/bold red]"

# Upload speed.
            try:
                if u < 0.8: u = f"Upload: [bold red]{u}[/bold red] Mbps"
                elif 0.8 <= u <= 1.5: u = f"Upload: [yellow]{u}[/yellow] Mbps"
                elif u > 1.5: u = f"Upload: [bold green]{u}[/bold green] Mbps"
            except:
                u = f"Upload: [bold red]Failure[/bold red]"
# Ping.
            try:
                if p >= 250: p = f"Ping: [bold red]{p}[/bold red] ms"
                elif 60 <= p < 250: p = f"Ping: [yellow]{p}[/yellow] ms"
                elif p < 60: p = f"Ping: [bold green]{p}[/bold green] ms"
            except:
                p = f"Ping: [bold red]Failure[/bold red]"
# Result.
            console2.print(Panel.fit(f"{d}\n{u}\n{p}\n\nYour IP: {c.get('ip')}\nProvider: " + \
                                     f"{c.get('isp')}\nLocation: {c.get('country')}",
                                     title="[cyan]🌐 Network Test[/cyan]", style=STL(color="cyan")))
            console2.log("[cyan]--> completed")
        except Exception:
            console2.print(f"[bold red]Network anomalies (internet_censorship?).\nTest will be skipped...")
