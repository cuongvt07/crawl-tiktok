import typer
import datetime
import platform
import os
from . import downloader
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from typer.models import OptionInfo

app = typer.Typer()
console = Console()

@app.command()
def download(
    url: str = typer.Argument(..., help="The TikTok video URL to download."),
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy server to use (e.g., http://user:pass@host:port).")
):
    """Download a TikTok video from the given URL."""
    console.print(f"Starting download for: {url}")
    with console.status("[bold green]Downloading...[/bold green]"):
        success, message = downloader.download_video(url, proxy)
        if not success and message == "IP_BLOCKED":
            console.print(Panel(
                Text("Your IP address seems to be blocked by TikTok. Please try again with a proxy.\n" 
                     "Example: [yellow]python main.py --proxy \"socks4://your_proxy_address:port\"[/yellow]",
                     justify="center"
                ),
                title="[bold red]Download Failed[/bold red]",
                border_style="red"
            ))
        elif not success:
            console.print(Panel(
                Text(f"Download failed: {message}", justify="center"),
                title="[bold red]Download Failed[/bold red]",
                border_style="red"
            ))
        else:
            console.print(Panel(
                Text(f"[bold green]{message}[/bold green]", justify="center"),
                title="[bold green]Download Successful[/bold green]",
                border_style="green"
            ))

@app.command()
def info(
    url: str = typer.Argument(..., help="The TikTok video URL to get information from."),
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy server to use (e.g., http://user:pass@host:port).")
):
    """Get information about a TikTok video without downloading it."""
    console.print(f"Getting info for: {url}")
    with console.status("[bold green]Fetching info...[/bold green]"):
        success, message = downloader.get_video_info(url, proxy)
        if not success:
            console.print(Panel(
                Text(f"Failed to get info: {message}", justify="center"),
                title="[bold red]Info Retrieval Failed[/bold red]",
                border_style="red"
            ))

@app.command()
def user_videos(
    user_url: str = typer.Argument(..., help="The TikTok user URL to download all videos from."),
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy server to use (e.g., http://user:pass@host:port).")
):
    """Download all videos from a given TikTok user URL."""
    console.print(f"Starting download for user videos from: {user_url}")
    with console.status("[bold green]Downloading user videos...[/bold green]"):
        success, message = downloader.download_user_videos(user_url, proxy)
        if not success and message == "IP_BLOCKED":
            console.print(Panel(
                Text("Your IP address seems to be blocked by TikTok. Please try again with a proxy.\n" 
                     "Example: [yellow]python main.py --proxy \"socks4://your_proxy_address:port\"[/yellow]",
                     justify="center"
                ),
                title="[bold red]Download Failed[/bold red]",
                border_style="red"
            ))
        elif not success:
            console.print(Panel(
                Text(f"Download failed: {message}", justify="center"),
                title="[bold red]Download Failed[/bold red]",
                border_style="red"
            ))
        else:
            console.print(Panel(
                Text(f"[bold green]{message}[/bold green]", justify="center"),
                title="[bold green]Download Successful[/bold green]",
                border_style="green"
            ))

@app.callback()
def main(
    proxy: str = typer.Option(None, "--proxy", "-p", help="Proxy server to use (e.g., http://user:pass@host:port).")
):
    """
    TikTok Video Downloader CLI.
    Enter a TikTok video URL to download.
    """
    if isinstance(proxy, OptionInfo):
        proxy = None

    today_date = datetime.date.today().strftime("%A, %d %B %Y")
    operating_system = platform.system()
    current_directory = os.getcwd()

    cli_info = f"""Today's date is: {today_date}
My operating system is: {operating_system}
I'm currently working in the directory: {current_directory}"""

    welcome_message = Panel(
        Text(f"""Welcome to TiktokCrawler!

{cli_info}

Enter 'exit' to quit.""", justify="left"),
        title="[bold green]TiktokCrawler CLI[/bold green]",
        border_style="blue"
    )
    console.print(welcome_message)

    # Display available commands
    console.print("""
[bold yellow]Available Commands:[/bold yellow]
  - [cyan]download <url>[/cyan]: Download a TikTok video.
  - [cyan]info <url>[/cyan]: Get information about a TikTok video.
  - [cyan]user-videos <user_url>[/cyan]: Download all videos from a TikTok user.
  - [cyan]--proxy <proxy_address>[/cyan]: Use a proxy for any command.

[bold yellow]Example Usage:[/bold yellow]
  - [green]tiktok-crawler download "https://www.tiktok.com/@user/video/123"[/green]
  - [green]tiktok-crawler info "https://www.tiktok.com/@user/video/123" -p "http://proxy:port"[/green]
  - [green]tiktok-crawler user-videos "https://www.tiktok.com/@user"[/green]

[bold yellow]Interactive Mode:[/bold yellow]
  - Just type a TikTok video URL to download it directly.
  - Type 'exit' to quit.""")
    while True:
        video_url = Prompt.ask("[bold cyan]Enter TikTok video URL[/bold cyan]")
        if video_url.lower() == 'exit':
            break

        with console.status("[bold green]Downloading...[/bold green]") as status:
            success, message = downloader.download_video(video_url, proxy)
            if not success and message == "IP_BLOCKED":
                console.print(Panel(
                    Text("Your IP address seems to be blocked by TikTok. Please try again with a proxy.",
                         "Example: [yellow]tiktok-crawler --proxy \"socks4://your_proxy_address:port\"[/yellow]",
                         justify="center"
                    ),
                    title="Download Failed",
                    border_style="red"
                ))
            elif not success:
                console.print(Panel(
                    Text(f"Download failed: {message}", justify="center"),
                    title="Download Failed",
                    border_style="red"
                ))
            else:
                console.print(Panel(
                    Text(f"{message}", justify="center"),
                    title="Download Successful",
                    border_style="green"
                ))

if __name__ == "__main__":
    typer.run(app)