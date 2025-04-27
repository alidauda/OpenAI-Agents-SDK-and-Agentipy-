import asyncio
from agentipy.agent import SolanaAgentKit
from agents import Agent, Runner, function_tool
from agentipy.tools.get_balance import BalanceFetcher
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from solders.pubkey import Pubkey
import os

# Initialize Rich console
console = Console()

# Initialize Solana agent
try:
    private_key = os.getenv("PRIVATE_KEY")
    solana_agent = SolanaAgentKit(
        private_key=private_key,
        rpc_url="https://api.mainnet-beta.solana.com"
    )
    wallet_address = str(solana_agent.wallet_address)
    console.print(f"[green]Successfully initialized Solana agent[/green]")
    console.print(f"[blue]Wallet address: {wallet_address}[/blue]")
except Exception as e:
    console.print(f"[red]Error initializing Solana agent: {str(e)}[/red]")
    raise

def validate_solana_address(address: str) -> bool:
    """Validate if a string is a valid Solana address."""
    try:
        Pubkey.from_string(address)
        return True
    except ValueError:
        return False

@function_tool
async def check_sol_balance() -> str:
    """Get the SOL balance for the current wallet."""
    try:
        balance = await BalanceFetcher.get_balance(solana_agent)
        if balance is None:
            return "Error: Could not fetch SOL balance"
        return f"SOL balance for {wallet_address}: {balance} SOL"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool
async def check_token_balance(token_address: str) -> str:
    """Get the token balance for a specific token.
    
    Args:
        token_address: The token address to check balance for
    """
    try:
        if not validate_solana_address(token_address):
            return "Error: Invalid token address format"
            
        token_pubkey = Pubkey.from_string(token_address)
        balance = await BalanceFetcher.get_balance(solana_agent, token_pubkey)
        if balance is None:
            return f"No balance found for token {token_address}"
        return f"Token balance for {wallet_address}: {balance} {token_address}"
    except Exception as e:
        return f"Error: {str(e)}"

agent = Agent(
    name="Solana Balance Checker",
    instructions=f"""You are a Solana blockchain assistant that can check balances for wallet {wallet_address}.
    
    Available commands:
    - For SOL balance: "Check my SOL balance"
    - For token balance: "Check balance for token <address>"
    
    Always use the appropriate function for each operation.""",
    tools=[check_sol_balance, check_token_balance],
)

async def main():
    console.print(Panel.fit(
        "[bold blue]Welcome to Solana Balance Checker[/bold blue]\n"
        f"[dim]Managing wallet: {wallet_address}[/dim]",
        border_style="blue"
    ))

    while True:
        console.print(Panel.fit(
            "[bold cyan]Available Operations[/bold cyan]\n\n"
            "1. Check Balance (SOL or Token)\n"
            "2. Exit",
            border_style="cyan"
        ))

        choice = Prompt.ask(
            "[bold green]Choose an operation[/bold green]",
            choices=["1", "2"]
        )
        
        try:
            if choice == "2":
                break
                
            if choice == "1":
                token_address = Prompt.ask("\n[bold green]Enter token address (press Enter for SOL balance)[/bold green]", default="")
                console.print("\n[yellow]🔍 Fetching balance...[/yellow]")
                
                if token_address and token_address.strip():
                    if not validate_solana_address(token_address):
                        console.print("[red]Error: Invalid token address format[/red]")
                        continue
                    result = await Runner.run(agent, input=f"Check balance for token {token_address}")
                else:
                    result = await Runner.run(agent, input="Check my SOL balance")
                
                console.print(Panel.fit(f"[bold green]{result.final_output}[/bold green]", border_style="green"))

            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

        except Exception as e:
            console.print(f"[red]Error occurred: {str(e)}[/red]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

    console.print("\n[blue]Thank you for using Solana Balance Checker! Goodbye![/blue]")

if __name__ == "__main__":
    asyncio.run(main())