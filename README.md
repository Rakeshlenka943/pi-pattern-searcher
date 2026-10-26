<div align="center">

<img src="assets/banner.svg" alt="Pi Pattern Searcher" width="100%" />

<br/>

# Pi Pattern Searcher

Find any number or word hidden inside the digits of π.

<p>
  <a href="https://github.com/Rakeshlenka943/pi-pattern-searcher/stargazers"><img src="https://img.shields.io/github/stars/Rakeshlenka943/pi-pattern-searcher?style=for-the-badge&logo=github" alt="GitHub stars" /></a>
  <a href="https://github.com/Rakeshlenka943/pi-pattern-searcher/actions"><img src="https://img.shields.io/github/actions/workflow/status/Rakeshlenka943/pi-pattern-searcher/ci.yml?branch=main&style=for-the-badge" alt="CI" /></a>
  <a href="https://pypi.org/project/pi-search/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License" /></a>
</p>

<a href="https://codespaces.new/Rakeshlenka943/pi-pattern-searcher">🚀 Open in GitHub Codespaces</a>

</div>

---

A fast, playful command-line tool that searches the digits of π for numbers, words, and patterns — without loading a giant text file into memory.

It tunes itself to your machine, picks the best backend, and searches efficiently using a smart mix of algorithms.

## Why this project is cool

Because π is infinite, intriguing, and full of patterns.

This project turns that idea into a practical search tool:

- Search for numbers like `14159`
- Search for words like `Hi` or `Aman`
- Run on Linux, macOS, and Windows
- Automatically benchmark your machine and choose the fastest setup
- Use a compiled C backend when available, with clean fallbacks

It feels part math puzzle, part systems project, and part benchmark experiment.

## Quick demo

```bash
pi-search 14159
pi-search --word Hi
pi-search 123456 --unlimited
```

Example output:

```text
$ pi-search 14159
Searching digits of π for: 14159
Found at digit index: 225,073
Match length: 5
Backend: c_ext
Time: 0.42s
```

## Installation

### Standard setup

```bash
git clone https://github.com/Rakeshlenka943/pi-pattern-searcher.git
cd pi-pattern-searcher
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -e ".[dev]"
pi-search
```

### Dependencies

On Linux, you may need build tools and GMP libraries:

```bash
# Debian / Ubuntu / Mint
sudo apt install -y python3-venv python3-dev build-essential \
                    libgmp-dev libmpfr-dev libmpc-dev pkg-config

# Fedora
sudo dnf install -y python3-devel gcc gmp-devel mpfr-devel libmpc-devel pkg-config

# Arch
sudo pacman -S --needed python gcc gmp mpfr libmpc pkg-config
```

On macOS:

```bash
xcode-select --install
brew install python gmp mpfr libmpc pkg-config
```

On Windows, install Python 3.10+ from python.org and use the standard venv flow above.

## Usage

```bash
pi-search                          # interactive menu
pi-search 14159                    # find a digit sequence
pi-search --word Hi                # find the ASCII-encoded word "Hi"
pi-search 42 --unlimited           # keep searching until found or RAM-cap reached
pi-search 123456 --progress        # show live progress
pi-search 999999 --save-on-found pi.txt
```

## Features

- Search any numeric sequence inside π
- Search ASCII-encoded words as well
- Auto-select the best backend for your machine
- Use a compiled C backend for better speed when available
- Benchmark hardware and cache a winning configuration
- Supports naive, KMP, and Rabin–Karp algorithms depending on pattern size
- Includes an interactive menu when run without arguments
- Works with unlimited search mode for larger pattern searches
- Includes rotating ASCII banner art and a playful CLI feel

## How it works

The tool does not read a gigantic static text file.

Instead, it:

1. Detects your machine and available CPU features
2. Measures backend performance
3. Chooses the fastest configuration for your setup
4. Generates π on demand
5. Searches with the right algorithm for the pattern length
6. Reports the match position and confidence estimate

This makes it lighter, faster, and more adaptive than simply scanning a prebuilt file.

## Performance

On a test laptop with an Intel i3-8130U, the C backend delivered a clear speedup at the most common sizes:

| Digits | mpmath | c_ext | Speedup |
|---|---:|---:|---:|
| 1M | 2.05s | 0.55s | 3.7x |
| 5M | 4.26s | 4.08s | ~1.05x |

The tuner chooses the fastest available backend based on your hardware and workload.

## Why this is useful

This project is great for:

- math enthusiasts exploring π
- algorithm experiments
- benchmarking code and hardware
- EDU demos and curious one-off searches
- browser-free local tooling for number pattern hunting

It turns a very abstract mathematical idea into something concrete and searchable.

## Roadmap

- [x] Search numbers and words in π
- [x] Hardware detection and autotuning
- [x] FAST C backend using GMP + Chudnovsky generation
- [x] Interactive CLI menu and unlimited mode
- [ ] File-cached generation for repeated large searches
- [ ] Multithreaded search
- [ ] Aho–Corasick multi-pattern matching
- [ ] PyPI release and optional CUDA backend

## Contributing

Contributions are welcome.

If you want to add features, improve the tuning logic, improve docs, or optimize the search path, open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

Made with curiosity, math, and a little obsession with π.

If this project helped you, give it a star ⭐

[![GitHub stars](https://img.shields.io/github/stars/Rakeshlenka943/pi-pattern-searcher?style=social)](https://github.com/Rakeshlenka943/pi-pattern-searcher/stargazers)

