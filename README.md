## Security Tools

### Secret Scanner

The project includes a secret scanning tool to prevent accidentally committing sensitive information to the repository.

To set up the pre-commit hook:

```bash
# Install the pre-commit hook
python tools/setup_git_hooks.py
```

To manually scan for secrets:

```bash
# Run the scanner manually
python tools/secret_scanner.py --path .
```

### Bypassing the Secret Scanner

If the secret scanner is blocking your commit and you need to bypass it:

```bash
# Bypass pre-commit hook temporarily for one commit
git commit --no-verify -m "Your commit message"
```

⚠️ **Warning**: Only bypass the scanner when you're absolutely certain no sensitive data is being committed.

#### Handling False Positives

If you encounter false positives in the scanner:

1. Review the reported issues carefully
2. Update the ignore patterns in `tools/secret_scanner.py` if needed
3. For test data that resembles secrets, add a comment `# NOSONAR` on the same line
4. Consider extracting the values to environment variables

```python
# Example of marking false positive
PASSWORD = "example_password"  # NOSONAR - This is test data, not a real password
```

The scanner checks for:
- API keys and tokens
- Database credentials
- Connection strings
- AWS credentials
- Other common sensitive information patterns

Always use environment variables for storing sensitive information, not hardcoded values.
