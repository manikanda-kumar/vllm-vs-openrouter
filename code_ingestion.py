import logging
from gitingest import ingest
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_github_repo(repo_url: str):
    logger.info(f"Starting repository ingestion for: {repo_url}")

    # Define patterns to exclude non-code files
    exclude_patterns = {
        # Documentation
        "*.md",
        "*.txt",
        "*.rst",
        "*.adoc",

        # Environment and config
        ".env*",
        "*.env",
        ".envrc",

        # Build and dependencies
        "node_modules/**",
        "venv/**",
        "env/**",
        ".venv/**",
        "__pycache__/**",
        "*.pyc",
        "dist/**",
        "build/**",
        "*.egg-info/**",

        # IDE and editor
        ".vscode/**",
        ".idea/**",
        "*.swp",
        "*.swo",

        # Version control
        ".git/**",
        ".gitignore",
        ".gitattributes",

        # CI/CD
        ".github/**",
        ".gitlab-ci.yml",

        # Package managers
        "package-lock.json",
        "yarn.lock",
        "poetry.lock",
        "Pipfile.lock",

        # Images and media
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.gif",
        "*.svg",
        "*.ico",
        "*.pdf",

        # Other
        "LICENSE",
        "*.log",
    }

    # Define patterns to include (code files only)
    include_patterns = {
        "*.py",
        "*.js",
        "*.ts",
        "*.tsx",
        "*.jsx",
        "*.java",
        "*.cpp",
        "*.c",
        "*.h",
        "*.hpp",
        "*.cs",
        "*.go",
        "*.rs",
        "*.rb",
        "*.php",
        "*.swift",
        "*.kt",
        "*.scala",
        "*.r",
        "*.sql",
        "*.sh",
        "*.bash",
        "*.html",
        "*.css",
        "*.scss",
        "*.sass",
        "*.json",
        "*.yaml",
        "*.yml",
        "*.xml",
        "*.toml",
    }

    logger.info(f"Excluding patterns: {exclude_patterns}")
    logger.info(f"Including patterns: {include_patterns}")

    try:
        logger.info("Calling gitingest to process repository...")
        summary, structure, content = ingest(
            repo_url,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )

        logger.info(f"Repository ingestion successful")
        logger.info(f"  Summary length: {len(summary) if summary else 0} chars")
        logger.info(f"  Structure length: {len(structure) if structure else 0} chars")
        logger.info(f"  Content length: {len(content) if content else 0} chars")

        context = {
            "summary": summary,
            "structure": structure,
            "content": content
        }

        return context
    except Exception as e:
        logger.error(f"Error ingesting repository {repo_url}: {str(e)}", exc_info=True)
        raise Exception(f"Error ingesting repository: {str(e)}") 