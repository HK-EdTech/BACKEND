# Terraform

## 1 - Initial Terrform LOCAL Setup
1. Setup HasiCorp tap first locally (via homebrew due to mac env)

```bash
    miltonchow:Macmini ~/PROJECTS/BACKEND $ terraform
    bash: terraform: command not found
    miltonchow:Macmini ~/PROJECTS/BACKEND $ brew --version
    Homebrew 5.0.4
    miltonchow:Macmini ~/PROJECTS/BACKEND $ brew tap hashicorp/tap
    ==> Auto-updating Homebrew...
    Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
    `$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
    ==> Downloading https://ghcr.io/v2/homebrew/core/portable-ruby/blobs/sha256:1c98fa49eacc935640a6f8e10a2bf33f14cfc276804b71ddb658ea45ba99d167
    ####################                                                                                                  18.0%#################################################################################                                     69.9%####################################################################################                                  72.5%#################################################################################################################### 100.0%
    ==> Pouring portable-ruby-3.4.8.arm64_big_sur.bottle.tar.gz
    ==> Homebrew collects anonymous analytics.
    Read the analytics documentation (and how to opt-out) here:
    https://docs.brew.sh/Analytics
    No analytics have been recorded yet (nor will be during this `brew` run).

    ==> Homebrew is run entirely by unpaid volunteers. Please consider donating:
    https://github.com/Homebrew/brew#donations

    ==> Auto-updated Homebrew!
    Updated 2 taps (homebrew/core and homebrew/cask).
    ==> New Formulae
    adplay: Command-line player for OPL2 music
    any2fasta: Convert various sequence formats to FASTA
    astra: Command-Line Interface for DataStax Astra
    av1an: Cross-platform command-line encoding framework
    azure-dev: Developer CLI that provides commands for working with Azure resources
    azurite: Lightweight server clone of Azure Storage that simulates it locally
    beads: Memory upgrade for your coding agent
    beads_viewer: Terminal-based UI for the Beads issue tracker
    bookokrat: Terminal EPUB Book Reader
    calm-cli: CLI allows you to interact with the Common Architecture Language Model (CALM)
    cargo-features-manager: TUI like cli tool to manage the features of your rust-project dependencies
    ccextractor: Tool for extracting closed captions from video files
    cek: Explore the (overlay) filesystem and layers of OCI container images
    cinecli: Browse, inspect, and launch movie torrents directly from your terminal
    classifier: Text classification with Bayesian, LSI, Logistic Regression, and kNN
    codanna: Code intelligence system with semantic search
    codex-acp: Use Codex from ACP-compatible clients such as Zed!
    cronboard: Terminal-based dashboard for managing cron jobs locally and on servers
    ctags-lsp: LSP implementation using universal-ctags as backend
    ctre: Compile-time PCRE-compatible regular expression matcher for C++
    dbcsr: Distributed Block Compressed Sparse Row matrix library
    depot: Build your Docker images in the cloud
    dnspyre: CLI tool for a high QPS DNS benchmark
    docker-language-server: Language server for Dockerfiles, Compose files, and Bake files
    dotnet@9: .NET Core
    dovi_convert: Dolby Vision Profile 7 to 8.1 MKV converter
    durdraw: Versatile ASCII and ANSI Art text editor for drawing in the terminal
    ekphos: Terminal-based markdown research tool inspired by Obsidian
    fence: Lightweight sandbox for commands with network and filesystem restrictions
    ffmpeg-full: Play, record, convert, and stream many audio and video codecs
    flecs: Fast entity component system for C & C++
    fzf-tab: Replace zsh completion selection menu with fzf
    garage: S3 object store so reliable you can run it outside datacenters
    gastown: Multi-agent workspace manager
    ghc@9.12: Glorious Glasgow Haskell Compilation System
    git-get: Better way to clone, organize and manage multiple git repositories
    git-pages: Scalable static site server for Git forges
    git-pages-cli: Tool for publishing a site to a git-pages server
    global-arrays: Partitioned Global Address Space (PGAS) library for distributed arrays
    gnuastro: Astronomical data manipulation and analysis utilities and libraries
    gogcli: Google Suite CLI
    graphqlite: SQLite graph database extension
    gup: Update binaries installed by go install
    hayagriva: Bibliography management tool
    hdrhistogram_c: C port of the HdrHistogram
    headscale-cli: CLI for headscale, an open-source implementation of the Tailscale control server
    headson: Head/tail for structured data
    helix-db: Open-source graph-vector database built from scratch in Rust
    hindent: Haskell pretty printer
    imagemagick-full: Tools and libraries to manipulate images in many formats
    jsonfmt: Like gofmt, but for JSON files
    karakeep: CLI tool for self-hostable bookmark-everything app karakeep
    khaos: Kafka traffic simulator for observability and chaos engineering
    klog: Command-line tool for time tracking in a human-readable, plain-text file format
    kubefwd: Bulk port forwarding Kubernetes services for local development
    kubernetes-cli@1.34: Kubernetes command-line interface
    kyua: Testing framework for infrastructure software
    ladybug: Embedded graph database built for query speed and scalability
    leetsolv: CLI tool for DSA problem revision with spaced repetition
    libevdev: Wrapper library for evdev devices
    libigloo: Generic C framework used and developed by the Icecast project
    libks: Foundational support for signalwire C products
    libthai: Thai language support library
    lispkit: Scheme framework for extension and scripting languages on macOS and iOS
    litra: Control Logitech Litra lights from the command-line
    llhttp: Port of http_parser to llparse
    mac-cleanup-go: TUI macOS cleaner that scans caches/logs and lets you select what to delete
    macchanger: Change your mac address, for macOS
    magics: ECMWF's meteorological plotting software
    mapscii: Whole World In Your Console
    mcp-scan: Constrain, log and scan your MCP connections for security vulnerabilities
    minizign: Minisign reimplemented in Zig
    mistral-vibe: Minimal CLI coding agent
    mlx-c: C API for MLX
    mole: Deep clean and optimize your Mac
    mq: Jq-like command-line tool for markdown processing
    mufetch: Neofetch-style music cli
    nativefiledialog-extended: Native file dialog library with C and C++ bindings
    neo4j-mcp: Neo4j official Model Context Protocol server for AI tools
    netshow: Interactive network connection monitor with friendly service names
    nkt: TUI for fast and simple interacting with your BibLaTeX database
    octodns: Tools for managing DNS across multiple providers
    openskills: Universal skills loader for AI coding agents
    oxfmt: High-performance formatting tool for JavaScript and TypeScript
    pake: Turn any webpage into a desktop app with Rust with ease
    papis: Powerful command-line document and bibliography manager
    patchpal: AI Assisted Patch Backporting Tool Frontend
    pgroll: Postgres zero-downtime migrations made easy
    pixlet: App runtime and UX toolkit for pixel-based apps
    pocket-tts: Text-to-speech application designed to run efficiently on CPUs
    pony-language-server: Language server for Pony
    pvetui: Terminal UI for Proxmox VE
    qo: Interactive minimalist TUI to query JSON, CSV, and TSV using SQL
    rad: Modern CLI scripts made easy
    radicle: Sovereign code forge built on Git
    ralph-orchestrator: Multi-agent orchestration framework for autonomous AI task completion
    redu: Ncdu for your restic repository
    repeater: Flashcard program that uses spaced repetition
    rig-r: R Installation Manager
    rockcraft: Tool to create OCI images using the language from Snapcraft and Charmcraft
    ruby@3.4: Powerful, clean, object-oriented scripting language
    rv-r: Declarative R package manager
    sandvault: Run AI agents isolated in a sandboxed macOS user account
    shiki: Beautiful yet powerful syntax highlighter
    signalwire-client-c: SignalWire C Client SDK
    slicot: Fortran subroutines library for systems and control
    snitch: Prettier way to inspect network connections
    superseedr: BitTorrent Client in your Terminal
    svu: Semantic version utility
    talm: Manage Talos Linux configurations the GitOps way
    tfclean: Remove applied moved block, import block, etc
    tftp-now: Single-binary TFTP server and client that you can use right now
    tock: Powerful time tracking tool for the command-line
    topydo: Todo list application using the todo.txt format
    tpix: Simple terminal image viewer using the Kitty graphics protocol
    tree-sitter@0.25: Incremental parsing library
    tronbyt-server: Manage your apps on your Tronbyt (flashed Tidbyt) completely locally
    ty: Extremely fast Python type checker, written in Rust
    vacuum: World's fastest OpenAPI & Swagger linter
    vampire: High-performance theorem prover
    vtsls: LSP wrapper for typescript extension of vscode
    wasm-bindgen: Facilitating high-level interactions between Wasm modules and JavaScript
    whosthere: LAN discovery tool with a modern TUI written in Go
    wifitui: Fast featureful friendly wifi terminal UI
    wik: View Wikipedia pages from your terminal
    witr: Why is this running?
    worktrunk: CLI for Git worktree management, designed for parallel AI agent workflows
    wuchale: Protobuf-like i18n from plain code
    xcsift: Swift tool to parse xcodebuild output for coding agents

    You have 7 outdated formulae installed.

    ==> Tapping hashicorp/tap
    Cloning into '/opt/homebrew/Library/Taps/hashicorp/homebrew-tap'...
    remote: Enumerating objects: 6284, done.
    remote: Counting objects: 100% (1047/1047), done.
    remote: Compressing objects: 100% (297/297), done.
    remote: Total 6284 (delta 915), reused 754 (delta 750), pack-reused 5237 (from 2)
    Receiving objects: 100% (6284/6284), 1.10 MiB | 4.26 MiB/s, done.
    Resolving deltas: 100% (4515/4515), done.
    Tapped 2 casks and 32 formulae (99 files, 1.5MB).
```

2. Install Terrform from hashicorp
```bash
    miltonchow:Macmini ~/PROJECTS/BACKEND $ brew install hashicorp/tap/terraform
    ==> Auto-updating Homebrew...
    Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
    `$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
    ==> Fetching downloads for: terraform
    ✔︎ Formula terraform (1.14.4)                                                                    Verified     28.7MB/ 28.7MB
    ==> Installing terraform from hashicorp/tap
    Error: Your Command Line Tools are too outdated.
    Update them from Software Update in System Settings.

    If that doesn't show you any updates, run:
    sudo rm -rf /Library/Developer/CommandLineTools
    sudo xcode-select --install

    Alternatively, manually download them from:
    https://developer.apple.com/download/all/.
    You should download the Command Line Tools for Xcode 26.0.
```

3. Optional: delete and update command line tools for xcode select

```bash
    sudo rm -rf /Library/Developer/CommandLineTools
    sudo xcode-select --install
```

4. Optional: Rerun `brew doctor` to ensure `Warning: Your Command Line Tools are too outdated.` warning logs are gone. Then rerun `brew tap hashicorp/tap` and `brew install hashicorp/tap/terraform`

```bash
    miltonchow:Macmini ~/PROJECTS/BACKEND $ brew tap hashicorp/tap
    ✔︎ JSON API cask.jws.json                                                                        Downloaded   15.3MB/ 15.3MB
    ✔︎ JSON API formula.jws.json                                                                     Downloaded   32.0MB/ 32.0MB
    miltonchow:Macmini ~/PROJECTS/BACKEND $ brew install hashicorp/tap/terraform
    ==> Auto-updating Homebrew...
    Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
    `$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
    ==> Fetching downloads for: terraform
    ✔︎ Formula terraform (1.14.4)                                                                    Verified     28.7MB/ 28.7MB
    ==> Installing terraform from hashicorp/tap
    🍺  /opt/homebrew/Cellar/terraform/1.14.4: 5 files, 95.6MB, built in 3 seconds
    ==> Running `brew cleanup terraform`...
    Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
    Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
    ==> `brew cleanup` has not been run in the last 30 days, running now...
    Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
    Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
    Removing: /Users/miltonchow/Library/Caches/Homebrew/portable-ruby-3.4.7.arm64_big_sur.bottle.tar.gz... (12.2MB)
    Removing: /Users/miltonchow/Library/Caches/Homebrew/portable-ruby-3.4.8.arm64_big_sur.bottle.tar.gz... (12.2MB)
    Removing: /Users/miltonchow/Library/Caches/Homebrew/openjdk@17_bottle_manifest--17.0.4.1_1... (10.5KB)
    Removing: /Users/miltonchow/Library/Caches/Homebrew/openjdk@17--17.0.4.1_1... (187.7MB)
    Removing: /Users/miltonchow/Library/Caches/Homebrew/bootsnap/42e939983ed75547f42207cad9f1e0fde134291f63f94bcb8df8abbd25416d42... (636 files, 5.5MB)
    Removing: /Users/miltonchow/Library/Logs/Homebrew/openjdk@17... (64B)
    Removing: /Users/miltonchow/Library/Logs/Homebrew/openssl@3... (64B)
    Removing: /Users/miltonchow/Library/Logs/Homebrew/ca-certificates... (64B)
    Removing: /opt/homebrew/var/homebrew/tmp/.cellar/libidn2... (79 files, 957.2KB)
    Removing: /opt/homebrew/var/homebrew/tmp/.cellar/mpdecimal... (21 files, 654.8KB)
    Removing: /opt/homebrew/var/homebrew/tmp/.cellar/libunistring... (58 files, 5.8MB)
    Removing: /opt/homebrew/var/homebrew/tmp/.cellar/expat... (22 files, 721.2KB)
    Removing: /opt/homebrew/var/homebrew/tmp/.cellar/readline... (55 files, 2.7MB)
    Removing: /opt/homebrew/var/homebrew/tmp/.cellar/lz4... (23 files, 729.1KB)
```

5. et volia

```bash
    miltonchow:Macmini ~/PROJECTS/BACKEND $ terraform --version
    Terraform v1.14.4
    on darwin_arm64
```

## 2 - Initial AWS cli Setup

1. `brew install awscli` (This takes like 20 mins)
2. AWS Console --> Top right "User" --> Security Credentials --> Create Access Key --> I underderstand...
    - Note:
    - AWS account ID: 213157792220
3. Configure the AWS cli: `aws configure`
    - 
    ```bash
        miltonchow:Macmini ~/PROJECTS/BACKEND $ aws configure
        AWS Access Key ID [****************ret:]: AKIATxxxxxxxHVMNY
        AWS Secret Access Key [None]: zKxxxxxeKi*********xx*xxDomxx*xxxxx*
        Default region name [AWS account ID: None]: ap-southeast-2
        Default output format [Access Key ID: None]: table
    ```
4. Verify your aws config with `aws sts get-caller-identity`
```bash
    miltonchow:Macmini ~/PROJECTS/BACKEND $ aws sts get-caller-identity
    --------------------------------------------------------------------
    |                         GetCallerIdentity                        |
    +--------------+----------------------------------+----------------+
    |    Account   |               Arn                |    UserId      |
    +--------------+----------------------------------+----------------+
    |  213157792220|  arn:aws:iam::213157792220:root  |  213157792220  |
    +--------------+----------------------------------+----------------+
```

4. Populate your main.tf, variables.tf, terraform.tfvars (that is git ignored)
5. `terraform init` to init the directory
6. `terraform plan` to see the upcoming changes
    ```bash
        miltonchow:Macmini ~/PROJECTS/BACKEND/terraform/aws $ terraform plan

        No changes. Your infrastructure matches the configuration.

        Terraform has compared your real infrastructure against your configuration and found no differences, so no changes are
        needed.
        ╷
        │ Warning: Value for undeclared variable
        │ 
        │ The root module does not declare a variable named "instance_type" but a value was found in file "terraform.tfvars". If
        │ you meant to use this value, add a "variable" block to the configuration.
        │ 
        │ To silence these warnings, use TF_VAR_... environment variables to provide certain "global" settings to all
        │ configurations in your organization. To reduce the verbosity of these warnings, use the -compact-warnings option.
        ╵
        ╷
        │ Warning: Value for undeclared variable
        │ 
        │ The root module does not declare a variable named "server_name" but a value was found in file "terraform.tfvars". If you
        │ meant to use this value, add a "variable" block to the configuration.
        │ 
        │ To silence these warnings, use TF_VAR_... environment variables to provide certain "global" settings to all
        │ configurations in your organization. To reduce the verbosity of these warnings, use the -compact-warnings option.
    ```

7. I removed `terraform.tfvars` and re-ran `terraform plan`, now works
    - 
    ```bash
        miltonchow:Macmini ~/PROJECTS/BACKEND/terraform/aws $ terraform plan

        No changes. Your infrastructure matches the configuration.

        Terraform has compared your real infrastructure against your configuration and found no differences, so no changes are
        needed.  
    ```
8. `terraform apply -auto-approve`