# Configuration Template Guide

This template shows how to configure the Git History Logbook tool for your repositories.

## Quick Setup

1. Copy `config.template.json` to `config.json`
2. Update the repository URLs to match your projects
3. Customize project names and author filtering as needed
4. Run the tool: `export_history.bat` (Windows) or `python git_history_logbook.py --config config.json`

## Configuration Sections

### 📁 Repositories

Each repository entry requires:

```json
{
  "name": "repository-name",          // Required: Short name for the repo
  "url": "https://github.com/...",    // Required: Git URL (HTTPS/SSH) or local path
  "description": "Project description", // Optional: Brief description
  "project": "ProjectName"            // Required: Project category/group
}
```

**Supported URL formats:**
- HTTPS: `https://github.com/username/repo`
- SSH: `git@github.com:username/repo.git`
- Local: `/path/to/local/repo` or `C:\path\to\repo`

### 🕒 Default Filters

```json
{
  "default_filters": {
    "since": "2021-01-01",    // Start date (YYYY-MM-DD)
    "until": "2025-12-31",    // End date (YYYY-MM-DD)  
    "author": null,           // Specific author or null for all
    "branch": null            // Specific branch or null for all branches
  }
}
```

### 👥 Selected Authors (Optional)

Filter commits to only include specific contributors:

```json
{
  "selected_authors": [
    "John Doe",
    "jane.smith", 
    "developer-username"
  ]
}
```

**Important notes:**
- Author names must match exactly as they appear in git commits
- If this section is empty or missing, ALL authors will be included
- Case-sensitive matching
- Use `git log --format="%an" | sort | uniq` to see actual author names in your repos

### ⚙️ Output Settings

```json
{
  "output_settings": {
    "default_format": "csv",     // Default output format
    "include_summary": true,     // Include summary statistics
    "parallel_workers": 4        // Number of concurrent repository processors
  }
}
```

## Project Categorization

Use the `project` field to group related repositories:

**Example project structures:**
```json
// Microservices architecture
"project": "Frontend"
"project": "Backend" 
"project": "API"
"project": "Database"

// Feature-based
"project": "UserManagement"
"project": "PaymentSystem"
"project": "Analytics"

// Technology-based  
"project": "WebApp"
"project": "SmartContracts"
"project": "Infrastructure"
"project": "Documentation"
```

## Example Configurations

### Simple Setup
```json
{
  "repositories": [
    {
      "name": "my-app",
      "url": "https://github.com/myorg/my-app",
      "description": "Main application",
      "project": "Core"
    }
  ],
  "default_filters": {
    "since": "2024-01-01",
    "until": "2024-12-31"
  }
}
```

### Multi-Project with Author Filtering
```json
{
  "repositories": [
    {
      "name": "web-frontend",
      "url": "https://github.com/company/web-frontend", 
      "project": "WebApp"
    },
    {
      "name": "mobile-app",
      "url": "https://github.com/company/mobile-app",
      "project": "Mobile" 
    },
    {
      "name": "blockchain-contracts",
      "url": "https://github.com/company/smart-contracts",
      "project": "Blockchain"
    }
  ],
  "selected_authors": [
    "Lead Developer",
    "senior.engineer",
    "DevOps Team"
  ],
  "default_filters": {
    "since": "2024-01-01"
  }
}
```

### Local Development Setup
```json
{
  "repositories": [
    {
      "name": "local-project",
      "url": "/home/user/projects/my-project",
      "project": "Development"
    },
    {
      "name": "remote-dependency", 
      "url": "https://github.com/upstream/library",
      "project": "Dependencies"
    }
  ]
}
```

## Tips & Best Practices

### 🎯 Repository Organization
- Use clear, consistent project names
- Group related repositories under the same project
- Include meaningful descriptions for context

### 👤 Author Filtering
- Run the tool without filtering first to see all contributor names
- Check author names carefully - they vary by git configuration
- Common variations: "John Doe", "john.doe", "jdoe@company.com"

### 📅 Date Filtering
- Use ISO date format: YYYY-MM-DD
- Set realistic date ranges to avoid processing unnecessary history
- Consider your repository's actual commit history range

### ⚡ Performance Optimization  
- Adjust `parallel_workers` based on your system (2-8 typically optimal)
- Use date filters to limit commit range for large repositories
- Local repositories process faster than remote clones

## Troubleshooting

### Common Issues

**Repository Access:**
- Ensure you have read access to all repositories
- For private repos, make sure SSH keys or tokens are configured
- Test repository URLs manually: `git clone <url>`

**Author Names Not Matching:**
- Use: `git log --format="%an" | sort | uniq` to see exact names
- Author names are case-sensitive
- Some repos may have inconsistent author formatting

**Performance Issues:**
- Reduce `parallel_workers` if system becomes unresponsive
- Add date filters to limit commit history range
- Check available disk space for temporary clones

**Network Issues:**
- Ensure stable internet connection for remote repositories
- Consider cloning large repos locally first for repeated analysis
- Increase timeout if repositories are slow to clone

## Security Notes

- **Never commit sensitive URLs** (with tokens) to public repositories
- Use SSH keys or personal access tokens for private repository access
- Be cautious with author names that might contain personal information
- Review generated reports before sharing publicly 