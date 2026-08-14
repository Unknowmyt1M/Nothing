import os
import sys
import subprocess
import threading
import queue
import time
import re
from datetime import datetime

# Force UTF-8 encoding on standard output/error, especially on Windows, to avoid UnicodeEncodeError with emojis
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.table import Table

# Initialize Rich Console
console = Console()

# Queue for logs to keep printing thread-safe and sequential
log_queue = queue.Queue()

# Store active process handles
backend_proc = None
frontend_proc = None

# Regex patterns for parsing and highlighting
HTTP_LOG_PATTERN = re.compile(
    r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})?.*?"(?P<method>GET|POST|PUT|DELETE|OPTIONS|PATCH|HEAD) (?P<path>.*?) HTTP/.*?" (?P<status>\d{3})'
)
TIME_PATTERN = re.compile(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[^\]]*?\]|\d{2}:\d{2}:\d{2}')

def get_status_style(status_code: str) -> str:
    """Return styling based on HTTP status code"""
    if status_code.startswith('2'):
        return "bold green"
    elif status_code.startswith('3'):
        return "bold cyan"
    elif status_code.startswith('4'):
        return "bold yellow"
    elif status_code.startswith('5'):
        return "bold red"
    return "white"

def format_log_line(line: str, source: str) -> Text:
    """Parse and style raw output lines from servers using Rich Text"""
    line = line.rstrip('\r\n')
    text = Text()

    # Prefix definitions
    if source == 'backend':
        prefix = Text("⚡ [Backend] │ ", style="cyan bold")
    else:
        prefix = Text("🌐 [Frontend] │ ", style="purple bold")
    
    text.append(prefix)

    # 1. Check for HTTP status and request patterns
    match = HTTP_LOG_PATTERN.search(line)
    if match:
        gd = match.groupdict()
        method = gd['method']
        path = gd['path']
        status = gd['status']
        
        # Style method
        method_style = "bold green" if method in ("GET", "HEAD") else "bold blue"
        status_style = get_status_style(status)

        # Highlight path parameters or full URLs
        path_text = f" {path} "
        
        # Build the styled log line
        log_content = Text()
        if gd['ip']:
            log_content.append(f"{gd['ip']} - - ", style="dim")
        
        log_content.append(f'"{method}', style=method_style)
        log_content.append(path_text, style="yellow")
        log_content.append('HTTP/1.1" ', style="dim")
        log_content.append(status, style=status_style)
        
        # Append remaining part of the line if any
        remaining = line[match.end():]
        if remaining:
            log_content.append(remaining, style="dim")
            
        text.append(log_content)
        return text

    # 2. Highlight generic log levels
    line_lower = line.lower()
    content_text = Text(line)
    
    if "error" in line_lower or "exception" in line_lower or "failed" in line_lower or "critical" in line_lower:
        content_text.stylize("bold red")
    elif "warning" in line_lower or "warn" in line_lower:
        content_text.stylize("yellow")
    elif "success" in line_lower or "compiled successfully" in line_lower:
        content_text.stylize("green")
    
    # 3. Next.js specific enhancements
    if source == 'frontend':
        if "▲ next.js" in line_lower:
            # Highlight Next logo
            line = line.replace("▲", "[bold purple]▲[/bold purple]")
            content_text = Text.from_markup(line)
        elif " ready in " in line_lower:
            # Highlight startup times
            line = re.sub(r'ready in (\d+(\.\d+)?s|ms)', r'[bold green]ready in \1[/bold green]', line, flags=re.IGNORECASE)
            content_text = Text.from_markup(line)
        elif " compiled " in line_lower:
            # Highlight compile times
            line = re.sub(r'(compiled .*? in \d+(\.\d+)?(s|ms))', r'[bold green]\1[/bold green]', line, flags=re.IGNORECASE)
            content_text = Text.from_markup(line)
        elif "○" in line:
            line = line.replace("○", "[bold yellow]○[/bold yellow]")
            content_text = Text.from_markup(line)
        elif "✓" in line:
            line = line.replace("✓", "[bold green]✓[/bold green]")
            content_text = Text.from_markup(line)

    # 4. Highlight timestamps
    # Find timestamps and color them dim cyan
    for m in TIME_PATTERN.finditer(content_text.plain):
        content_text.stylize("dim cyan", m.start(), m.end())

    text.append(content_text)
    return text

def enqueue_stream(stream, source):
    """Read a stream line by line and put it in the queue"""
    try:
        for line in iter(stream.readline, ''):
            if not line:
                break
            log_queue.put((source, line))
    except Exception:
        pass
    finally:
        stream.close()

def kill_process(proc):
    """Cleanly terminate process and its descendants"""
    if not proc:
        return
    if os.name == 'nt':
        # On Windows, kill the process tree to prevent orphan cmd/node/python tasks
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
    else:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception:
            pass

def print_welcome_banner():
    """Prints a beautiful dashboard entry card using Rich"""
    welcome_text = Text()
    welcome_text.append("✨ NOTHING-MAIN UNIFIED DEVELOPER CONSOLE ✨\n\n", style="bold magenta")
    welcome_text.append("🚀 starting servers simultaneously...\n\n", style="italic")
    
    welcome_text.append("🌐 Frontend Dashboard: ", style="bold")
    welcome_text.append("http://localhost:5000\n", style="underline link purple")
    welcome_text.append("⚡ Backend API Check:  ", style="bold")
    welcome_text.append("http://localhost:3000/healthz\n\n", style="underline link cyan")

    welcome_text.append("💡 Hotkeys:\n", style="bold dim")
    welcome_text.append("   • Press [bold red]Ctrl + C[/bold red] in this terminal to stop both servers cleanly.\n", style="dim")

    panel = Panel(
        Align.center(welcome_text),
        border_style="bold magenta",
        title="[bold white]DownUpVid Multi-Server Runner[/bold white]",
        subtitle="[bold green]System Initialized[/bold green]",
        expand=False
    )
    console.print(panel)
    console.print()

def main():
    global backend_proc, frontend_proc
    
    # Clean screen and print welcome banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print_welcome_banner()

    # Get backend environment with python unbuffered to get live console output
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"

    # Start Backend API Server (FastAPI + Uvicorn on port 3000)
    console.print("🔧 [cyan]Spinning up Backend FastAPI Server...[/cyan]")
    try:
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "backend.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=backend_env,
            encoding='utf-8',
            errors='replace'
        )
    except Exception as e:
        console.print(f"❌ [bold red]Failed to start Backend Server: {e}[/bold red]")
        sys.exit(1)

    # Start Frontend Next.js Server
    console.print("🔧 [purple]Spinning up Frontend Next.js Server...[/purple]")
    try:
        # Use shell=True on Windows to resolve npm.cmd wrapper correctly
        use_shell = (os.name == 'nt')
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=use_shell,
            bufsize=1,
            env=os.environ,
            encoding='utf-8',
            errors='replace'
        )
    except Exception as e:
        console.print(f"❌ [bold red]Failed to start Frontend Server: {e}[/bold red]")
        kill_process(backend_proc)
        sys.exit(1)

    # Spawn thread workers to read stdout & stderr for both servers
    threads = [
        threading.Thread(target=enqueue_stream, args=(backend_proc.stdout, 'backend'), daemon=True),
        threading.Thread(target=enqueue_stream, args=(backend_proc.stderr, 'backend'), daemon=True),
        threading.Thread(target=enqueue_stream, args=(frontend_proc.stdout, 'frontend'), daemon=True),
        threading.Thread(target=enqueue_stream, args=(frontend_proc.stderr, 'frontend'), daemon=True),
    ]

    for t in threads:
        t.start()

    console.print("\n🎉 [bold green]Both servers launched successfully! Stream is live below:[/bold green]\n")
    console.print("─" * console.width, style="dim")

    try:
        while True:
            # Check if any process has exited unexpectedly
            b_status = backend_proc.poll()
            f_status = frontend_proc.poll()

            if b_status is not None:
                console.print(f"\n⚠️ [bold red]Backend process exited unexpectedly with code {b_status}[/bold red]")
                break
            if f_status is not None:
                console.print(f"\n⚠️ [bold red]Frontend process exited unexpectedly with code {f_status}[/bold red]")
                break

            # Print queued logs
            try:
                # Poll queue for logs (non-blocking sleep to keep CPU usage low)
                source, line = log_queue.get(timeout=0.1)
                formatted_text = format_log_line(line, source)
                console.print(formatted_text)
                log_queue.task_done()
            except queue.Empty:
                continue

    except KeyboardInterrupt:
        console.print("\n\n🛑 [bold yellow]Shutdown signal received! Terminating processes...[/bold yellow]")
    finally:
        # Shutdown routine
        console.print("🧹 [dim]Cleaning up subprocesses...[/dim]")
        
        # Kill processes
        kill_process(backend_proc)
        kill_process(frontend_proc)
        
        # Nice exit card
        exit_text = Text()
        exit_text.append("👋 Servers shut down successfully!\n", style="bold green")
        exit_text.append("All ports have been freed. See you next time! 😎", style="dim")
        
        console.print()
        console.print(
            Panel(
                Align.center(exit_text),
                border_style="green",
                expand=False
            )
        )

if __name__ == "__main__":
    main()
