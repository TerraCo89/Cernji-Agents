#!/usr/bin/env python3
"""
Analyze Claude Code chat history to:
- Identify repetitive research patterns
- Measure token/time usage
- Find knowledge gaps for Skills
- Track Skills and slash commands utilization
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re


class TranscriptAnalyzer:
    """Analyze Claude Code transcripts for patterns and optimization opportunities."""

    def __init__(self, time_range_days: Optional[int] = 7):
        self.time_range_days = time_range_days
        self.cutoff_date = datetime.now() - timedelta(days=time_range_days) if time_range_days else None

    def find_transcript_files(self) -> List[Path]:
        """Find all transcript files within the time range."""
        transcripts = []

        # Local project logs
        logs_dir = Path('logs')
        if logs_dir.exists():
            for session_dir in logs_dir.iterdir():
                if session_dir.is_dir():
                    for transcript in session_dir.glob('transcript_*.jsonl'):
                        if self._is_within_timerange(transcript):
                            transcripts.append(transcript)

        # Global Claude storage
        home = Path.home()
        claude_dir = home / '.claude' / 'projects'
        if claude_dir.exists():
            for jsonl_file in claude_dir.rglob('*.jsonl'):
                if self._is_within_timerange(jsonl_file):
                    transcripts.append(jsonl_file)

        return transcripts

    def _is_within_timerange(self, file_path: Path) -> bool:
        """Check if file modification time is within the specified time range."""
        if self.cutoff_date is None:
            return True

        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return mtime >= self.cutoff_date
        except Exception:
            return False

    def parse_transcript(self, transcript_path: Path) -> List[Dict]:
        """Parse JSONL transcript file."""
        events = []
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error parsing {transcript_path}: {e}", file=sys.stderr)

        return events

    def extract_token_usage(self, events: List[Dict]) -> Dict[str, int]:
        """Extract token usage from transcript events."""
        total_input = 0
        total_output = 0
        cache_reads = 0
        cache_creation = 0

        for event in events:
            if event.get('type') == 'assistant':
                usage = event.get('message', {}).get('usage', {})
                total_input += usage.get('input_tokens', 0)
                total_output += usage.get('output_tokens', 0)
                cache_reads += usage.get('cache_read_input_tokens', 0)
                cache_creation += usage.get('cache_creation_input_tokens', 0)

        return {
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'cache_read_tokens': cache_reads,
            'cache_creation_tokens': cache_creation,
            'total_tokens': total_input + total_output,
        }

    def analyze_tool_usage(self, events: List[Dict]) -> Counter:
        """Analyze tool usage patterns."""
        tool_counter = Counter()

        for event in events:
            if event.get('type') == 'assistant':
                content = event.get('message', {}).get('content', [])
                for item in content:
                    if item.get('type') == 'tool_use':
                        tool_name = item.get('name')
                        if tool_name:
                            tool_counter[tool_name] += 1

        return tool_counter

    def extract_skill_usage(self, events: List[Dict]) -> Counter:
        """Extract Skill tool invocations."""
        skill_counter = Counter()

        for event in events:
            if event.get('type') == 'assistant':
                content = event.get('message', {}).get('content', [])
                for item in content:
                    if item.get('type') == 'tool_use' and item.get('name') == 'Skill':
                        skill_input = item.get('input', {})
                        skill_name = skill_input.get('skill', '')
                        if skill_name:
                            skill_counter[skill_name] += 1

        return skill_counter

    def extract_command_usage(self, events: List[Dict]) -> Counter:
        """Extract SlashCommand tool invocations."""
        command_counter = Counter()

        for event in events:
            if event.get('type') == 'assistant':
                content = event.get('message', {}).get('content', [])
                for item in content:
                    if item.get('type') == 'tool_use' and item.get('name') == 'SlashCommand':
                        cmd_input = item.get('input', {})
                        command = cmd_input.get('command', '')
                        if command:
                            # Extract command name (remove parameters)
                            cmd_name = command.split()[0] if command else ''
                            if cmd_name:
                                command_counter[cmd_name] += 1

        return command_counter

    def detect_repetitive_patterns(self, events: List[Dict]) -> List[Tuple[str, int]]:
        """Detect repetitive tool usage patterns that could be optimized."""
        patterns = []

        # Extract sequences of tool calls
        tool_sequences = []
        current_sequence = []

        for event in events:
            if event.get('type') == 'assistant':
                content = event.get('message', {}).get('content', [])
                for item in content:
                    if item.get('type') == 'tool_use':
                        tool_name = item.get('name')
                        if tool_name:
                            current_sequence.append(tool_name)
            elif event.get('type') == 'user' and current_sequence:
                # End of assistant turn
                if len(current_sequence) > 1:
                    tool_sequences.append(tuple(current_sequence))
                current_sequence = []

        # Count sequence patterns
        sequence_counter = Counter(tool_sequences)

        # Find patterns that appear multiple times
        for sequence, count in sequence_counter.most_common(10):
            if count >= 2:
                pattern_str = ' → '.join(sequence)
                patterns.append((pattern_str, count))

        return patterns

    def find_knowledge_gaps(self, events: List[Dict]) -> List[Tuple[str, int]]:
        """Identify repeated questions or research topics."""
        # Look for Task tool calls with specific patterns
        task_topics = []

        for event in events:
            if event.get('type') == 'assistant':
                content = event.get('message', {}).get('content', [])
                for item in content:
                    if item.get('type') == 'tool_use' and item.get('name') == 'Task':
                        task_input = item.get('input', {})
                        description = task_input.get('description', '')
                        subagent = task_input.get('subagent_type', '')

                        if description:
                            # Normalize description
                            normalized = description.lower().strip()
                            task_topics.append(f"{subagent}: {normalized}" if subagent else normalized)

        # Also look for common grep patterns
        grep_patterns = []
        for event in events:
            if event.get('type') == 'assistant':
                content = event.get('message', {}).get('content', [])
                for item in content:
                    if item.get('type') == 'tool_use' and item.get('name') == 'Grep':
                        grep_input = item.get('input', {})
                        pattern = grep_input.get('pattern', '')
                        if pattern:
                            grep_patterns.append(f"grep: {pattern}")

        # Count occurrences
        topic_counter = Counter(task_topics + grep_patterns)

        # Return topics that appear 2+ times
        gaps = [(topic, count) for topic, count in topic_counter.most_common(20) if count >= 2]
        return gaps

    def get_available_skills(self) -> List[str]:
        """Get list of available Skills in the project."""
        skills = []
        skills_dir = Path('.claude/skills')

        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skills.append(skill_dir.name)

        return sorted(skills)

    def get_available_commands(self) -> List[str]:
        """Get list of available slash commands in the project."""
        commands = []
        commands_dir = Path('.claude/commands')

        if commands_dir.exists():
            for cmd_file in commands_dir.glob('*.md'):
                # Command name is filename without .md extension
                cmd_name = f"/{cmd_file.stem}"
                commands.append(cmd_name)

        return sorted(commands)

    def analyze_all_transcripts(self) -> Dict:
        """Analyze all transcripts and return comprehensive report data."""
        transcripts = self.find_transcript_files()

        if not transcripts:
            return {
                'error': 'No transcripts found',
                'transcripts_count': 0
            }

        # Aggregate data
        total_tokens = defaultdict(int)
        all_tool_usage = Counter()
        all_skill_usage = Counter()
        all_command_usage = Counter()
        all_patterns = []
        all_gaps = []

        for transcript_path in transcripts:
            events = self.parse_transcript(transcript_path)
            if not events:
                continue

            # Token usage
            tokens = self.extract_token_usage(events)
            for key, value in tokens.items():
                total_tokens[key] += value

            # Tool usage
            tool_usage = self.analyze_tool_usage(events)
            all_tool_usage.update(tool_usage)

            # Skill usage
            skill_usage = self.extract_skill_usage(events)
            all_skill_usage.update(skill_usage)

            # Command usage
            command_usage = self.extract_command_usage(events)
            all_command_usage.update(command_usage)

            # Patterns
            patterns = self.detect_repetitive_patterns(events)
            all_patterns.extend(patterns)

            # Knowledge gaps
            gaps = self.find_knowledge_gaps(events)
            all_gaps.extend(gaps)

        # Get available resources
        available_skills = self.get_available_skills()
        available_commands = self.get_available_commands()

        # Calculate utilization
        used_skills = set(all_skill_usage.keys())
        unused_skills = set(available_skills) - used_skills

        used_commands = set(all_command_usage.keys())
        unused_commands = set(available_commands) - used_commands

        return {
            'transcripts_count': len(transcripts),
            'time_range_days': self.time_range_days,
            'token_usage': dict(total_tokens),
            'tool_usage': dict(all_tool_usage.most_common(20)),
            'skill_usage': dict(all_skill_usage.most_common()),
            'command_usage': dict(all_command_usage.most_common()),
            'available_skills': available_skills,
            'available_commands': available_commands,
            'unused_skills': sorted(unused_skills),
            'unused_commands': sorted(unused_commands),
            'repetitive_patterns': self._aggregate_patterns(all_patterns),
            'knowledge_gaps': self._aggregate_gaps(all_gaps),
        }

    def _aggregate_patterns(self, patterns: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """Aggregate repetitive patterns across sessions."""
        pattern_counter = Counter()
        for pattern, count in patterns:
            pattern_counter[pattern] += count
        return pattern_counter.most_common(10)

    def _aggregate_gaps(self, gaps: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """Aggregate knowledge gaps across sessions."""
        gap_counter = Counter()
        for gap, count in gaps:
            gap_counter[gap] += count
        return gap_counter.most_common(10)


def format_report(data: Dict) -> str:
    """Format analysis data into a readable report."""
    if 'error' in data:
        return f"❌ Error: {data['error']}"

    time_range = f"Last {data['time_range_days']} days" if data['time_range_days'] else "All time"
    lines = [
        f"📊 Chat History Analysis ({time_range})",
        f"Analyzed {data['transcripts_count']} transcript(s)",
        "",
    ]

    # Token usage
    tokens = data['token_usage']
    total_tokens = tokens.get('total_tokens', 0)
    input_tokens = tokens.get('total_input_tokens', 0)
    output_tokens = tokens.get('total_output_tokens', 0)
    cache_reads = tokens.get('cache_read_tokens', 0)

    # Rough cost estimate (Sonnet 4.5 pricing)
    cost_input = (input_tokens / 1_000_000) * 3.0
    cost_output = (output_tokens / 1_000_000) * 15.0
    total_cost = cost_input + cost_output

    lines.extend([
        "💰 Token Usage:",
        f"  - Total: {total_tokens:,} tokens (${total_cost:.2f})",
        f"  - Input: {input_tokens:,} tokens (${cost_input:.2f})",
        f"  - Output: {output_tokens:,} tokens (${cost_output:.2f})",
        f"  - Cache reads: {cache_reads:,} tokens (saved)",
        "",
    ])

    # Top tools
    tool_usage = data.get('tool_usage', {})
    if tool_usage:
        lines.append("🔧 Top Tools Used:")
        for tool, count in list(tool_usage.items())[:10]:
            lines.append(f"  - {tool}: {count} uses")
        lines.append("")

    # Skills utilization
    skill_usage = data.get('skill_usage', {})
    available_skills = data.get('available_skills', [])
    unused_skills = data.get('unused_skills', [])

    lines.append(f"📚 Skills Utilization ({len(available_skills)} available):")

    if skill_usage:
        lines.append("  ✅ Used:")
        for skill, count in list(skill_usage.items())[:10]:
            lines.append(f"    - {skill}: {count} use(s)")
    else:
        lines.append("  ⚠️  No Skills were used in this period")

    if unused_skills:
        lines.append("  ❌ Never Used:")
        for skill in unused_skills[:10]:
            lines.append(f"    - {skill}")

    lines.append("")

    # Commands utilization
    command_usage = data.get('command_usage', {})
    available_commands = data.get('available_commands', [])
    unused_commands = data.get('unused_commands', [])

    lines.append(f"🎯 Slash Commands Utilization ({len(available_commands)} available):")

    if command_usage:
        lines.append("  ✅ Used:")
        for command, count in list(command_usage.items())[:10]:
            lines.append(f"    - {command}: {count} use(s)")
    else:
        lines.append("  ⚠️  No slash commands were used in this period")

    if unused_commands:
        lines.append("  ❌ Never Used:")
        for command in unused_commands[:15]:
            lines.append(f"    - {command}")
        if len(unused_commands) > 15:
            lines.append(f"    ... and {len(unused_commands) - 15} more")

    lines.append("")

    # Repetitive patterns
    patterns = data.get('repetitive_patterns', [])
    if patterns:
        lines.append("🔄 Repetitive Patterns Found:")
        for pattern, count in patterns[:5]:
            lines.append(f"  - {pattern} ({count} occurrences)")
            # Suggest optimization
            if 'Grep' in pattern and 'Read' in pattern:
                lines.append(f"    💡 Could be optimized with pre-indexed search")
        lines.append("")

    # Knowledge gaps
    gaps = data.get('knowledge_gaps', [])
    if gaps:
        lines.append("🎓 Knowledge Gaps (Repeated Research Topics):")
        for gap, count in gaps[:10]:
            lines.append(f"  - {gap} ({count} times)")
        lines.append("")

    # Recommendations
    lines.append("💡 Recommendations:")

    recommendations = []

    # Check for unused skills
    if len(unused_skills) > len(available_skills) * 0.5:
        recommendations.append(f"Review {len(unused_skills)} unused Skills - consider deprecating or improving documentation")

    # Check for unused commands
    if len(unused_commands) > len(available_commands) * 0.5:
        recommendations.append(f"Review {len(unused_commands)} unused slash commands - consider consolidating or documenting better")

    # Check for knowledge gaps that could be Skills
    high_frequency_gaps = [gap for gap, count in gaps if count >= 3]
    if high_frequency_gaps:
        recommendations.append(f"Create Skills for {len(high_frequency_gaps)} frequently researched topics")

    # Check for repetitive patterns
    if patterns:
        recommendations.append("Optimize repetitive tool sequences with Skills or custom commands")

    if not recommendations:
        recommendations.append("No major optimization opportunities found - good job! 🎉")

    for i, rec in enumerate(recommendations, 1):
        lines.append(f"  {i}. {rec}")

    return '\n'.join(lines)


def main():
    """Main entry point."""
    import argparse

    # Fix Windows console encoding
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if sys.stderr:
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    parser = argparse.ArgumentParser(description='Analyze Claude Code chat history')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7, use 0 for all time)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON data instead of formatted report')

    args = parser.parse_args()

    time_range = args.days if args.days > 0 else None
    analyzer = TranscriptAnalyzer(time_range_days=time_range)

    data = analyzer.analyze_all_transcripts()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        report = format_report(data)
        print(report)


if __name__ == '__main__':
    main()
