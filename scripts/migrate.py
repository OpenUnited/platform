#!/usr/bin/env python
import click
from pathlib import Path
from template_analyzer import TemplateDependencyGraph
from template_converter import StagedConverter
from template_tester import TemplateTestSuite
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import sys

console = Console()

@click.group()
def cli():
    """Django Template Migration Toolkit"""
    pass

@cli.command()
@click.argument('template_dir', type=click.Path(exists=True))
def analyze(template_dir):
    """Analyze templates and create dependency graph"""
    with console.status("[bold green]Analyzing templates..."):
        graph = TemplateDependencyGraph()
        graph.analyze_templates(Path(template_dir))
    
    # Create results table
    table = Table(title="Template Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    
    table.add_row("Total templates", str(len(graph.nodes)))
    table.add_row("Base templates", str(len(graph.base_templates)))
    
    high_complexity = [t for t in graph.nodes.values() if t.complexity_score > 10]
    table.add_row("High complexity templates", str(len(high_complexity)))
    
    console.print(table)
    
    # Save conversion order
    order = graph.get_conversion_order()
    order_file = Path('conversion_order.txt')
    order_file.write_text('\n'.join(order))
    
    rprint("[green]Conversion order saved to conversion_order.txt[/green]")

@cli.command()
@click.argument('template_path', type=click.Path(exists=True))
@click.option('--stage', type=click.Choice(['urls', 'static', 'filters', 'inheritance']))
@click.option('--auto-approve', is_flag=True, help="Apply changes without confirmation")
def convert(template_path, stage, auto_approve):
    """Convert a single template"""
    template_path = Path(template_path)
    converter = StagedConverter(template_path)
    
    with console.status(f"[bold green]Converting {stage} in {template_path.name}..."):
        success, message = converter.convert_stage(stage)
    
    if success:
        console.print("\n[bold]Preview of changes:[/bold]")
        console.print(converter.preview_changes())
        
        if auto_approve or click.confirm("Apply these changes?"):
            error = converter.commit_changes()
            if error:
                console.print(f"[red]Error: {error}[/red]")
            else:
                console.print("[green]Changes applied successfully[/green]")
                
                # Run tests
                test_suite = TemplateTestSuite(template_path)
                results = test_suite.run_tests()
                
                if all(results.values()):
                    console.print("[green]All tests passed![/green]")
                else:
                    console.print("[yellow]Warning: Some tests failed:[/yellow]")
                    for test, passed in results.items():
                        status = "✓" if passed else "✗"
                        color = "green" if passed else "red"
                        console.print(f"[{color}]{status} {test}[/{color}]")
    else:
        console.print(f"[red]Error: {message}[/red]")

@cli.command()
@click.argument('template_dir', type=click.Path(exists=True))
@click.option('--auto-approve', is_flag=True, help="Apply changes without confirmation")
def convert_all(template_dir, auto_approve):
    """Convert all templates in the correct order"""
    if not Path('conversion_order.txt').exists():
        console.print("[yellow]Please run 'analyze' command first[/yellow]")
        sys.exit(1)
    
    templates = Path('conversion_order.txt').read_text().splitlines()
    stages = ['urls', 'static', 'filters', 'inheritance']
    
    with console.status("[bold green]Converting templates...") as status:
        for template in templates:
            for stage in stages:
                status.update(f"Converting {stage} in {template}")
                click.echo(f"\nProcessing {template} - {stage}")
                converter = StagedConverter(Path(template))
                success, message = converter.convert_stage(stage)
                
                if not success:
                    console.print(f"[red]Error converting {template}: {message}[/red]")
                    if not click.confirm("Continue with next template?"):
                        sys.exit(1)

if __name__ == '__main__':
    cli()