#!/usr/bin/env python3
"""
CLI interface for Resume Agent.

Provides command-line access to resume optimization functionality.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from resume_agent_langgraph import run_resume_agent, resume_from_checkpoint
#from resume_agent.config import get_settings


def load_resume_from_file(filepath: str) -> str:
    """Load resume text from file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {filepath}")
    
    return path.read_text(encoding='utf-8')


def save_resume_to_file(content: str, filepath: str) -> None:
    """Save resume content to file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"✓ Resume saved to: {filepath}")


def cmd_optimize(args):
    """Run resume optimization."""
    print("🚀 Starting Resume Optimization Agent")
    print("="*60)
    
    # Load resume
    resume_text = load_resume_from_file(args.resume)
    print(f"✓ Loaded resume from: {args.resume}")
    
    # Run agent
    result = run_resume_agent(
        resume_text=resume_text,
        job_posting_url=args.job_url,
        thread_id=args.thread_id,
        max_iterations=args.max_iterations,
    )
    
    # Save output if provided
    if args.output:
        if result.get('final_resume'):
            save_resume_to_file(result['final_resume'], args.output)
        else:
            print("⚠️  No final resume yet (waiting for approval)")
            print(f"   Thread ID: {args.thread_id}")
    
    return 0


def cmd_resume(args):
    """Resume from checkpoint."""
    print(f"▶️  Resuming optimization for thread: {args.thread_id}")
    print("="*60)
    
    result = resume_from_checkpoint(args.thread_id)
    
    # Save output
    if args.output and result.get('final_resume'):
        save_resume_to_file(result['final_resume'], args.output)
    
    return 0


def cmd_visualize(args):
    """Visualize the agent graph."""
    from resume_agent.graphs import create_resume_agent_graph
    
    try:
        graph = create_resume_agent_graph()
        
        # Try to generate visualization
        try:
            from IPython.display import Image, display
            display(Image(graph.get_graph().draw_mermaid_png()))
            print("✓ Graph visualization displayed")
        except ImportError:
            # Fallback to text representation
            print("📊 Resume Agent Graph Structure:")
            print("="*60)
            print(graph.get_graph().draw_ascii())
            print("\n(Install IPython for visual graph rendering)")
    except Exception as e:
        print(f"✗ Failed to visualize graph: {e}")
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Resume Agent - AI-powered resume optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize a resume for a job posting
  %(prog)s optimize --resume my_resume.txt --job-url https://example.com/job --output optimized.txt
  
  # Resume from checkpoint after manual review
  %(prog)s resume --thread-id my-session-123 --output final_resume.txt
  
  # Visualize the agent graph
  %(prog)s visualize
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize resume for job')
    optimize_parser.add_argument(
        '--resume', '-r',
        required=True,
        help='Path to resume file (txt, md, or docx)'
    )
    optimize_parser.add_argument(
        '--job-url', '-j',
        required=True,
        help='URL of job posting'
    )
    optimize_parser.add_argument(
        '--output', '-o',
        help='Output file path for optimized resume'
    )
    optimize_parser.add_argument(
        '--thread-id', '-t',
        default='default',
        help='Unique thread ID for this session (default: "default")'
    )
    optimize_parser.add_argument(
        '--max-iterations', '-m',
        type=int,
        default=3,
        help='Maximum optimization iterations (default: 3)'
    )
    optimize_parser.set_defaults(func=cmd_optimize)
    
    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume from checkpoint')
    resume_parser.add_argument(
        '--thread-id', '-t',
        required=True,
        help='Thread ID to resume'
    )
    resume_parser.add_argument(
        '--output', '-o',
        help='Output file path for final resume'
    )
    resume_parser.set_defaults(func=cmd_resume)
    
    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', help='Visualize agent graph')
    visualize_parser.set_defaults(func=cmd_visualize)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
