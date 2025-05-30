#!/usr/bin/env python3
"""
Git History Logbook - Combined Exporter and Generator
Export git commit history from multiple repositories and generate chronological logbooks.
"""

import os
import csv
import json
import logging
import argparse
import tempfile
import shutil
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHistoryLogbook:
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file) if config_file else {}
        self.temp_dirs = []
        
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return {}
    
    @contextmanager
    def _temp_directory(self):
        """Context manager for temporary directories with robust cleanup."""
        # Create local temp directory in current working directory
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        temp_dir = os.path.join(os.getcwd(), f"temp_git_clone_{timestamp}")
        
        # Ensure directory doesn't exist (very unlikely but safe)
        counter = 0
        original_temp_dir = temp_dir
        while os.path.exists(temp_dir):
            counter += 1
            temp_dir = f"{original_temp_dir}_{counter}"
        
        os.makedirs(temp_dir)
        self.temp_dirs.append(temp_dir)
        logger.info(f"Created local temp directory: {temp_dir}")
        
        try:
            yield temp_dir
        finally:
            self._cleanup_directory(temp_dir)
    
    def _cleanup_directory(self, directory: str):
        """Robust cleanup of temporary directories."""
        try:
            if os.path.exists(directory):
                # Try standard removal first
                shutil.rmtree(directory)
                logger.info(f"Cleaned up local temp directory: {os.path.basename(directory)}")
        except PermissionError:
            try:
                # Windows-specific cleanup for git directories
                subprocess.run(['rmdir', '/s', '/q', directory], 
                             shell=True, check=False, capture_output=True)
                logger.info(f"Cleaned up local temp directory (Windows): {os.path.basename(directory)}")
            except Exception as e:
                logger.warning(f"Could not clean up {os.path.basename(directory)}: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning up {os.path.basename(directory)}: {e}")
    
    def _clone_repository(self, repo_url: str, repo_name: str) -> Optional[str]:
        """Clone repository to temporary directory."""
        try:
            with self._temp_directory() as temp_dir:
                clone_path = os.path.join(temp_dir, repo_name)
                
                # Clone repository
                result = subprocess.run(
                    ['git', 'clone', repo_url, clone_path],
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to clone {repo_url}: {result.stderr}")
                    return None
                
                logger.info(f"Cloned {repo_url} to {clone_path}")
                return clone_path
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout cloning {repo_url}")
            return None
        except Exception as e:
            logger.error(f"Error cloning {repo_url}: {e}")
            return None
    
    def _get_commit_history(self, repo_path: str, repo_name: str, repo_project: str, **filters) -> List[Dict]:
        """Extract commit history from repository."""
        try:
            # Build git log command
            cmd = ['git', 'log', '--pretty=format:%H|%an|%ad|%s|%b', '--date=iso']
            
            # Add filters
            if filters.get('since'):
                cmd.extend(['--since', filters['since']])
            if filters.get('until'):
                cmd.extend(['--until', filters['until']])
            if filters.get('author'):
                cmd.extend(['--author', filters['author']])
            if filters.get('branch'):
                cmd.append(filters['branch'])
            else:
                cmd.append('--all')
            
            # Execute git log
            result = subprocess.run(
                cmd, cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Git log failed for {repo_name}: {result.stderr}")
                return []
            
            # Parse commits - split by lines and process each commit line
            commits = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                
                # Parse commit line
                parts = line.split('|', 4)
                if len(parts) < 4:
                    continue
                
                commit = {
                    'repository': repo_name,
                    'project': repo_project,
                    'hash': parts[0],
                    'author_name': parts[1],
                    'date': parts[2],
                    'subject': parts[3],
                    'body': parts[4] if len(parts) > 4 else ''
                }
                
                commits.append(commit)
            
            logger.info(f"Extracted {len(commits)} commits from {repo_name}")
            return commits
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting commit history for {repo_name}")
            return []
        except Exception as e:
            logger.error(f"Error getting commit history for {repo_name}: {e}")
            return []
    
    def _process_repository(self, repo_info: Dict, **filters) -> List[Dict]:
        """Process a single repository."""
        repo_name = repo_info.get('name', 'unknown')
        repo_url = repo_info.get('url', '')
        repo_project = repo_info.get('project', 'Unknown')
        
        if not repo_url:
            logger.error(f"No URL provided for repository: {repo_name}")
            return []
        
        logger.info(f"Processing repository: {repo_name}")
        
        # Handle local vs remote repositories
        if os.path.exists(repo_url):
            # Local repository
            return self._get_commit_history(repo_url, repo_name, repo_project, **filters)
        else:
            # Remote repository - clone first
            with self._temp_directory() as temp_dir:
                clone_path = os.path.join(temp_dir, repo_name)
                
                try:
                    # Clone repository 
                    result = subprocess.run(
                        ['git', 'clone', repo_url, clone_path],
                        capture_output=True, text=True, timeout=300
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to clone {repo_url}: {result.stderr}")
                        return []
                    
                    # Fetch all remote branches to get complete history
                    subprocess.run(
                        ['git', 'fetch', '--all'],
                        cwd=clone_path, capture_output=True, text=True, timeout=60
                    )
                    
                    logger.info(f"Cloned {repo_url} to {clone_path}")
                    return self._get_commit_history(clone_path, repo_name, repo_project, **filters)
                    
                except Exception as e:
                    logger.error(f"Error processing {repo_name}: {e}")
                    return []
    
    def export_history(self, repositories: List[Dict], **filters) -> List[Dict]:
        """Export commit history from multiple repositories."""
        all_commits = []
        workers = filters.get('parallel_workers', 4)
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all repository processing tasks
            future_to_repo = {
                executor.submit(self._process_repository, repo, **filters): repo
                for repo in repositories
            }
            
            # Collect results
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    commits = future.result()
                    all_commits.extend(commits)
                except Exception as e:
                    logger.error(f"Error processing {repo.get('name', 'unknown')}: {e}")
        
        # Filter by selected authors if configured
        if self.config.get('selected_authors') and len(self.config['selected_authors']) > 0:
            selected_authors = self.config['selected_authors']
            original_count = len(all_commits)
            all_commits = [commit for commit in all_commits if commit['author_name'] in selected_authors]
            logger.info(f"Filtered from {original_count} to {len(all_commits)} commits from selected authors")
        else:
            logger.info(f"No author filtering applied - using all {len(all_commits)} commits")
        
        # Sort by date (newest first)
        all_commits.sort(key=lambda x: x['date'], reverse=True)
        return all_commits
    
    def save_to_csv(self, commits: List[Dict], output_file: str):
        """Save commits to CSV file."""
        if not commits:
            logger.warning("No commits to save")
            return
        
        fieldnames = ['repository', 'project', 'hash', 'author_name', 'date', 'subject', 'body']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(commits)
        
        logger.info(f"Exported {len(commits)} commits to {output_file}")
    
    def _format_commit_entry(self, commit: Dict, format_type: str = "markdown") -> str:
        """Format a single commit entry."""
        try:
            parsed_date = datetime.strptime(commit['date'][:19], '%Y-%m-%d %H:%M:%S')
        except:
            parsed_date = datetime.now()
        
        date_str = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        hash_short = commit['hash'][:8]
        project = commit.get('project', 'Unknown')
        
        if format_type == "markdown":
            entry = f"**{date_str}** | `{project}` | `{commit['repository']}` | *{commit['author_name']}*\n"
            entry += f"{commit['subject']}\n"
            if commit.get('body') and commit['body'].strip():
                body_first_line = commit['body'].split('\n')[0].strip()
                if body_first_line and body_first_line != commit['subject']:
                    entry += f"> {body_first_line}\n"
            entry += f"`{hash_short}`\n\n"
            
        elif format_type == "html":
            entry = f"""
            <div class="commit-entry">
                <div class="commit-header">
                    <span class="date">{date_str}</span>
                    <span class="project">{project}</span>
                    <span class="repo">{commit['repository']}</span>
                    <span class="author">{commit['author_name']}</span>
                    <span class="hash">{hash_short}</span>
                </div>
                <div class="commit-subject">{commit['subject']}</div>
            """
            if commit.get('body') and commit['body'].strip():
                body_first_line = commit['body'].split('\n')[0].strip()
                if body_first_line and body_first_line != commit['subject']:
                    entry += f'<div class="commit-body">{body_first_line}</div>'
            entry += "</div>\n"
            
        return entry
    
    def generate_logbook(self, commits: List[Dict], base_name: str = "commit_log"):
        """Generate logbook from commits."""
        if not commits:
            logger.warning("No commits to generate logbook from")
            return []
        
        # Parse dates for all commits
        for commit in commits:
            try:
                commit['parsed_date'] = datetime.strptime(commit['date'][:19], '%Y-%m-%d %H:%M:%S')
            except:
                commit['parsed_date'] = datetime.now()
        
        # Sort by date (newest first)
        commits.sort(key=lambda x: x['parsed_date'], reverse=True)
        
        files_generated = []
        
        # Generate Markdown
        md_file = self._generate_markdown_log(commits, f"{base_name}.md")
        files_generated.append(md_file)
        
        # Generate HTML
        html_file = self._generate_html_log(commits, f"{base_name}.html")
        files_generated.append(html_file)
        
        return files_generated
    
    def _generate_markdown_log(self, commits: List[Dict], output_file: str):
        """Generate markdown commit log."""
        content = f"""# Commit History Log
*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*

Total commits: {len(commits):,}

---

"""
        
        # Group commits by month
        monthly_commits = defaultdict(list)
        for commit in commits:
            month_key = commit['parsed_date'].strftime('%Y-%m')
            monthly_commits[month_key].append(commit)
        
        # Sort months in reverse chronological order
        sorted_months = sorted(monthly_commits.keys(), reverse=True)
        
        for month in sorted_months:
            month_commits = monthly_commits[month]
            month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
            
            content += f"## {month_name} ({len(month_commits)} commits)\n\n"
            
            # Group by day within the month
            daily_commits = defaultdict(list)
            for commit in month_commits:
                day_key = commit['parsed_date'].strftime('%Y-%m-%d')
                daily_commits[day_key].append(commit)
            
            # Sort days in reverse chronological order
            sorted_days = sorted(daily_commits.keys(), reverse=True)
            
            for day in sorted_days:
                day_commits = daily_commits[day]
                day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%A, %B %d')
                
                content += f"### {day_name} ({len(day_commits)} commits)\n\n"
                
                for commit in day_commits:
                    content += self._format_commit_entry(commit, "markdown")
        
        content += f"""
---
*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Markdown commit log generated: {output_file}")
        return output_file
    
    def _generate_html_log(self, commits: List[Dict], output_file: str):
        """Generate HTML commit log."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Commit History Log - CrypTech</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 4px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        .commit-entry {{
            border: 1px solid #e1e8ed;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
            background: #fafbfc;
        }}
        .commit-header {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .date {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .project {{
            background: #f3e5f5;
            color: #7b1fa2;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .repo {{
            background: #e3f2fd;
            color: #1565c0;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .author {{
            color: #7b1fa2;
            font-style: italic;
        }}
        .hash {{
            font-family: 'Courier New', monospace;
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            color: #666;
        }}
        .commit-subject {{
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .commit-body {{
            font-size: 0.9em;
            color: #666;
            font-style: italic;
            margin-top: 5px;
        }}
        .stats {{
            background: #e8f5e8;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            text-align: center;
            color: #2e7d32;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        @media (max-width: 768px) {{
            .commit-header {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Commit History Log</h1>
        <p><em>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
        
        <div class="stats">
            Total commits: {len(commits):,}
        </div>
"""
        
        # Group commits by month
        monthly_commits = defaultdict(list)
        for commit in commits:
            month_key = commit['parsed_date'].strftime('%Y-%m')
            monthly_commits[month_key].append(commit)
        
        # Sort months in reverse chronological order
        sorted_months = sorted(monthly_commits.keys(), reverse=True)
        
        for month in sorted_months:
            month_commits = monthly_commits[month]
            month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
            
            html_content += f"<h2>{month_name} ({len(month_commits)} commits)</h2>"
            
            # Group by day within the month
            daily_commits = defaultdict(list)
            for commit in month_commits:
                day_key = commit['parsed_date'].strftime('%Y-%m-%d')
                daily_commits[day_key].append(commit)
            
            # Sort days in reverse chronological order
            sorted_days = sorted(daily_commits.keys(), reverse=True)
            
            for day in sorted_days:
                day_commits = daily_commits[day]
                day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%A, %B %d')
                
                html_content += f"<h3>{day_name} ({len(day_commits)} commits)</h3>"
                
                for commit in day_commits:
                    html_content += self._format_commit_entry(commit, "html")
        
        html_content += f"""
        <div class="footer">
            <p>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML commit log generated: {output_file}")
        return output_file
    
    def cleanup_temp_directories(self):
        """Clean up all temporary directories."""
        if self.temp_dirs:
            logger.info(f"Cleaning up {len(self.temp_dirs)} local temp directories...")
        for temp_dir in self.temp_dirs:
            self._cleanup_directory(temp_dir)
        self.temp_dirs.clear()

def main():
    parser = argparse.ArgumentParser(description='Export git history and generate chronological logbooks')
    parser.add_argument('--config', help='Configuration file (JSON)')
    parser.add_argument('--repos', nargs='+', help='Repository paths or URLs')
    parser.add_argument('--output', default='commit_log', help='Base name for output files')
    parser.add_argument('--csv', help='Save CSV file (optional)')
    parser.add_argument('--since', help='Show commits since date (YYYY-MM-DD)')
    parser.add_argument('--until', help='Show commits until date (YYYY-MM-DD)')
    parser.add_argument('--author', help='Filter by author name')
    parser.add_argument('--branch', help='Specific branch to analyze')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Initialize the logbook generator
    logbook = GitHistoryLogbook(args.config)
    
    try:
        # Get repositories from config or command line
        repositories = []
        
        if args.config and logbook.config.get('repositories'):
            repositories = logbook.config['repositories']
        elif args.repos:
            repositories = [{'name': os.path.basename(repo), 'url': repo} for repo in args.repos]
        else:
            print("❌ Error: No repositories specified. Use --config or --repos")
            return 1
        
        print(f"🚀 Processing {len(repositories)} repositories...")
        
        # Build filters
        filters = {
            'since': args.since,
            'until': args.until,
            'author': args.author,
            'branch': args.branch,
            'parallel_workers': args.workers
        }
        
        # Use default filters from config if available and no CLI filters specified
        if args.config and logbook.config.get('default_filters'):
            config_filters = logbook.config['default_filters']
            if not args.since and config_filters.get('since'):
                filters['since'] = config_filters['since']
            if not args.until and config_filters.get('until'):
                filters['until'] = config_filters['until']
            if not args.author and config_filters.get('author'):
                filters['author'] = config_filters['author']
            if not args.branch and config_filters.get('branch'):
                filters['branch'] = config_filters['branch']
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Export commit history
        commits = logbook.export_history(repositories, **filters)
        
        if not commits:
            print("❌ No commits found")
            return 1
        
        print(f"📊 Collected {len(commits)} commits")
        
        # Save CSV if requested
        if args.csv:
            logbook.save_to_csv(commits, args.csv)
        
        # Generate logbook
        print("📋 Generating commit history logbook...")
        files_generated = logbook.generate_logbook(commits, args.output)
        
        print(f"\n🎉 Complete! Generated files:")
        for file in files_generated:
            print(f"  📁 {file}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        # Always cleanup temporary directories
        logbook.cleanup_temp_directories()

if __name__ == "__main__":
    exit(main()) 