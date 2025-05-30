# Git History Logbook

A comprehensive tool for exporting git commit history from multiple repositories and generating chronological logbooks with project categorization and author filtering.

## Features

- **Multi-repository support**: Process both local paths and remote URLs (HTTPS/SSH)
- **Project categorization**: Group repositories by project (e.g., Neptune, Denom)
- **Author filtering**: Optional filtering by selected contributors
- **Parallel processing**: Configurable worker threads for speed
- **Multiple output formats**: Markdown and HTML logbooks
- **Advanced filtering**: Date ranges, authors, branches
- **Configuration-driven**: JSON config files or command-line arguments
- **Automatic cleanup**: Robust temporary directory management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Repositories

Edit `config.json` to specify your repositories:

```json
{
  "repositories": [
    {
      "name": "my-project",
      "url": "https://github.com/user/my-project", 
      "description": "My awesome project",
      "project": "MainProject"
    }
  ],
  "default_filters": {
    "since": "2021-01-01",
    "until": "2025-12-31"
  },
  "selected_authors": [
    "developer1",
    "developer2"
  ]
}
```

### 3. Generate Logbook

**Windows (Easy):**
```cmd
export_history.bat
```

**Command Line:**
```bash
python git_history_logbook.py --config config.json --output my_logbook
```

## Configuration

### Repository Configuration

Each repository entry supports:

```json
{
  "name": "repository-name",
  "url": "https://github.com/user/repo",
  "description": "Optional description",
  "project": "ProjectName"
}
```

### Author Filtering (Optional)

Add `selected_authors` to filter commits by specific contributors:

```json
{
  "selected_authors": [
    "John Doe",
    "Jane Smith",
    "developer_username"
  ]
}
```

**Note**: If `selected_authors` is empty or not present, all commits from all authors will be included.

### Complete Configuration Example

```json
{
  "repositories": [
    {
      "name": "neptune-webapp",
      "url": "https://github.com/user/neptune-webapp",
      "description": "Frontend application",
      "project": "Neptune"
    },
    {
      "name": "validator-scripts", 
      "url": "https://github.com/user/validator-scripts",
      "description": "Chain validation tools",
      "project": "Denom"
    }
  ],
  "default_filters": {
    "since": "2021-01-01",
    "until": "2025-12-31",
    "author": null,
    "branch": null
  },
  "selected_authors": [
    "mat",
    "biest",
    "Will Stahl",
    "Kyle King"
  ],
  "output_settings": {
    "default_format": "csv",
    "include_summary": true,
    "parallel_workers": 4
  }
}
```

## Usage

### Basic Usage

```bash
# Use config file
python git_history_logbook.py --config config.json

# Specify repositories directly
python git_history_logbook.py --repos https://github.com/user/repo1 /path/to/local/repo2

# With filters
python git_history_logbook.py --config config.json --since 2024-01-01 --author "John Doe"
```

### Command Line Options

- `--config`: Configuration file (JSON)
- `--repos`: Repository paths or URLs (space-separated)
- `--output`: Base name for output files (default: commit_log)
- `--csv`: Save CSV file (optional)
- `--since`: Show commits since date (YYYY-MM-DD)
- `--until`: Show commits until date (YYYY-MM-DD)
- `--author`: Filter by author name
- `--branch`: Specific branch to analyze
- `--workers`: Number of parallel workers (default: 4)

## Output Formats

### Markdown Logbook
- Clean chronological format
- Organized by month and day
- Shows **Project** | **Repository** | **Author** for each commit
- Includes commit details and short hashes
- Perfect for documentation

### HTML Logbook
- Professional web-ready format
- Modern responsive design
- Color-coded projects, repositories and authors
- Interactive and printable

### CSV Export (Optional)
- Raw data for further analysis
- Includes project information
- Compatible with Excel and other tools
- All commit metadata included

## Examples

### Generate logbook with project categorization:
```bash
python git_history_logbook.py --config config.json --output project_history
```

### Filter by specific date range:
```bash
python git_history_logbook.py --config config.json --since 2024-01-01 --until 2024-12-31
```

### Save CSV and generate logbook:
```bash
python git_history_logbook.py --config config.json --csv history.csv --output project_log
```

## Files Generated

When you run the tool, it generates timestamped files:

- `commit_logbook_YYYY-MM-DD_HH-MM.md` - Markdown logbook
- `commit_logbook_YYYY-MM-DD_HH-MM.html` - HTML logbook  
- `commits_YYYY-MM-DD_HH-MM.csv` - CSV data (if --csv specified)

## Requirements

- Python 3.7+
- Git installed and accessible from command line
- Internet connection for remote repositories
- Dependencies: pandas, openpyxl

## Troubleshooting

### Common Issues

1. **Git not found**: Ensure Git is installed and in your PATH
2. **Permission errors**: Run as administrator on Windows if needed
3. **Network timeouts**: Check internet connection for remote repos
4. **Memory issues**: Reduce parallel workers for large repositories
5. **Author filtering**: Ensure author names match exactly as they appear in git commits

### Windows-Specific Notes

- Uses robust cleanup for temporary directories
- Handles Windows file permission issues
- Batch script provided for easy execution
- **Local temp directories**: Creates temporary git clones in current directory for better isolation

## License

Apache 2.0 License - feel free to use and modify as needed. 
