# Nano-graphrag Project Setup Guide

## Project Structure

nano-graphrag/
├── docs/                      # Documentation
│   ├── CONTRIBUTING.md
│   ├── FAQ.md
│   └── …
├── examples/                  # Example usage and benchmarks
│   ├── benchmarks/
│   └── …
├── nano_graphrag/            # Main package
│   ├── init.py
│   ├── _storage/
│   └── …
├── tests/                    # Test suite
├── pyproject.toml           # Project configuration
└── uv.lock                  # Dependency lock file

## Prerequisites
- macOS (instructions may need adaptation for other operating systems)
- Homebrew package manager
- uv package manager (`pip install uv` or see [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/))

## Initial Setup

### 1. Python Environment Cleanup (Optional but Recommended)
If you have multiple Python versions that are causing conflicts:
```bash
# Remove problematic Python versions
brew uninstall --force python@3.13 python@3.12

# Ensure Python 3.11 is properly linked
brew unlink python@3.11 && brew link python@3.11

2. Verify Python Installation

First, check if Python 3.11.5 is available:

# Check available Python versions
uv python list | grep 3.11.5

# If Python 3.11.5 is not listed, install it
uv python install 3.11.5

3. LLVM Configuration

# Install LLVM 14 via Homebrew (required for llvmlite)
brew install llvm@14

# Set LLVM configuration
export LLVM_CONFIG=/opt/homebrew/opt/llvm@14/bin/llvm-config

# Add to shell profile for persistence
echo 'export LLVM_CONFIG=/opt/homebrew/opt/llvm@14/bin/llvm-config' >> ~/.zshrc

4. Environment Setup

# Clean up any existing environment (might need sudo if permission denied)
rm -rf .venv  # Use sudo if permission denied

# Create new environment with explicit Python version
UV_LINK_MODE=copy UV_DEBUG=1 uv venv --python 3.11.5

# Activate the environment
source .venv/bin/activate

# Verify correct Python version
python --version  # Should show Python 3.11.5

5. Initial Dependencies Installation

The first installation requires explicit Python version:

# Install all dependencies including development packages
UV_LINK_MODE=copy uv sync --python 3.11.5 --extra dev

6. Initial Verification

First test run should use explicit Python version:

# Run tests to verify everything is working
uv run --python 3.11.5 pytest -v

Development Workflow

Regular Usage

After initial setup, you can use shorter commands:

# Run all tests
uv run pytest -v

# Run specific tests
uv run pytest tests/test_rag.py -v

# Run with coverage
uv run pytest --cov=nano_graphrag

Adding New Dependencies

# Add a new runtime dependency
uv add package-name

# Add a new development dependency
uv add --group dev package-name

Common Issues and Solutions
	1.	Permission Issues

# If you see "Permission denied" when removing .venv
sudo rm -rf .venv


	2.	Python Version Problems
If you encounter Python version issues:

# Clean environment and recreate with explicit version
rm -rf .venv
UV_LINK_MODE=copy uv venv --python 3.11.5
source .venv/bin/activate
uv sync --python 3.11.5 --extra dev


	3.	File System Link Warning
If you see “Failed to clone files” warning:

# Add UV_LINK_MODE=copy to commands
UV_LINK_MODE=copy uv sync


	4.	LLVM Issues

# If you have conflicts with other LLVM versions
brew unlink llvm  # If you have a newer version
brew install llvm@14
export LLVM_CONFIG=/opt/homebrew/opt/llvm@14/bin/llvm-config


	5.	Invalid Environment
If you see “not a valid Python environment” error:

rm -rf .venv
UV_DEBUG=1 uv venv --python 3.11.5
source .venv/bin/activate
uv sync --python 3.11.5 --extra dev



Environment Variables Summary
	•	UV_LINK_MODE=copy: Prevents filesystem linking warnings
	•	UV_DEBUG=1: Provides detailed output for troubleshooting
	•	LLVM_CONFIG: Points to LLVM 14 installation

Initial vs Regular Usage
	•	During initial setup and troubleshooting, use --python 3.11.5 flag
	•	For regular development work, the shorter commands without the flag are sufficient
	•	If you encounter version issues, revert to using explicit version flag

Best Practices
	1.	Always use explicit Python version (--python 3.11.5) with uv commands
	2.	Verify Python version after environment activation
	3.	Use UV_DEBUG=1 when troubleshooting installation issues
	4.	Keep LLVM_CONFIG set in your environment
	5.	Clean and recreate environment if you encounter strange behavior

Maintenance Notes
	•	The project requires Python 3.11.x due to numba dependency constraints
	•	LLVM 14 is required for llvmlite compilation
	•	Key dependencies to monitor:
	•	graspologic and its dependency chain
	•	numba version compatibility
	•	llvmlite requirements

