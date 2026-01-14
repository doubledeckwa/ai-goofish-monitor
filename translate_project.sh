#!/bin/bash

# Script to translate all Chinese text in project files to English using translate-shell

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if trans is installed
if ! command -v trans &> /dev/null; then
    echo -e "${RED}Error: translate-shell (trans) is not installed${NC}"
    echo "Install it with: brew install translate-shell"
    exit 1
fi

# Function to translate Chinese text in a file
translate_file() {
    local file="$1"
    local temp_file=$(mktemp)
    local has_changes=false
    
    echo -e "${YELLOW}Processing: $file${NC}"
    
    # Use Python to process the file and translate Chinese text
    python3 - "$file" "$temp_file" << 'PYTHON_SCRIPT'
import sys
import re
import subprocess

def translate_text(text):
    """Translate Chinese text to English using translate-shell"""
    try:
        result = subprocess.run(
            ['trans', '-b', 'zh:en', text],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None

def translate_line(line):
    """Find and translate Chinese text in a line"""
    # Find all Chinese text segments (including punctuation and spaces between Chinese chars)
    pattern = r'[\u4e00-\u9fff]+[^\u4e00-\u9fff\u0020-\u007e]*[\u4e00-\u9fff]+|[\u4e00-\u9fff]+'
    matches = list(re.finditer(pattern, line))
    
    if not matches:
        return line, False
    
    new_line = line
    offset = 0
    changed = False
    
    for match in matches:
        chinese_text = match.group(0)
        translated = translate_text(chinese_text)
        
        if translated:
            # Replace in the line, adjusting for previous replacements
            start = match.start() + offset
            end = match.end() + offset
            new_line = new_line[:start] + translated + new_line[end:]
            offset += len(translated) - len(chinese_text)
            changed = True
    
    return new_line, changed

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    file_changed = False
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                new_line, line_changed = translate_line(line.rstrip('\n'))
                f_out.write(new_line + '\n')
                if line_changed:
                    file_changed = True
    
    sys.exit(0 if file_changed else 1)
except Exception as e:
    print(f"Error processing file: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

    if [ $? -eq 0 ]; then
        mv "$temp_file" "$file"
        echo -e "${GREEN}✓ Translated: $file${NC}"
    else
        rm "$temp_file"
        echo -e "${YELLOW}  No Chinese text found in: $file${NC}"
    fi
}

# Find all files with Chinese characters using Python (works on macOS)
echo -e "${GREEN}Finding files with Chinese text...${NC}"
files=$(python3 << 'PYTHON_SCRIPT'
import os
import re
from pathlib import Path

exclude_dirs = {'node_modules', '.git', 'dist', '__pycache__', '.venv', 'venv'}
exclude_exts = {'.pyc', '.lock', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def should_skip(path):
    parts = Path(path).parts
    if any(part in exclude_dirs for part in parts):
        return True
    if Path(path).suffix in exclude_exts:
        return True
    return False

found_files = []
for root, dirs, files in os.walk('.'):
    # Remove excluded directories from dirs list to prevent walking into them
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for file in files:
        filepath = os.path.join(root, file)
        if should_skip(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if has_chinese(content):
                    found_files.append(filepath)
        except (UnicodeDecodeError, PermissionError, IsADirectoryError):
            continue

for f in found_files:
    print(f)
PYTHON_SCRIPT
)

if [ -z "$files" ]; then
    echo -e "${YELLOW}No files with Chinese text found.${NC}"
    exit 0
fi

file_count=$(echo "$files" | wc -l | tr -d ' ')
echo -e "${GREEN}Found $file_count file(s) with Chinese text${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to translate all files? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Translation cancelled."
    exit 0
fi

# Process each file
count=0
for file in $files; do
    count=$((count + 1))
    echo -e "\n[${count}/${file_count}]"
    translate_file "$file"
    # Small delay to avoid rate limiting
    sleep 0.5
done

echo -e "\n${GREEN}Translation complete!${NC}"
