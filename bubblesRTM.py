from bubbles.cli.serve import main

# Redirect of entrypoint to the CLI.
# This is largely here as a shim until we shift to the 
# configured console script in pyproject.toml

if __name__ == "__main__":
    main()
