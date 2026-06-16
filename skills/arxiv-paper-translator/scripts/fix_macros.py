# fix_macros.py - Fix xeCJK catcode issues for custom macros followed by Chinese
# Usage: python fix_macros.py [main.tex]
#
# This script finds custom LaTeX macros followed by Chinese characters and inserts
# {} between the macro and the Chinese text to prevent xeCJK from parsing them
# as a single undefined command.
#
# Example: \method中文 -> \method{}中文

import re
import sys
import os

def fix_macros_in_file(filepath):
    """Fix custom macros followed by Chinese characters in a single file."""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Common custom macros that need {} separator when followed by Chinese
    # Add more as needed for specific papers
    macros = [
        'method', 'bfmodel', 'Doublequant', 'doublequant',
        'Pagedoptim', 'pagedoptim', 'benchv', 'benchoa', 'model',
        'ours', 'Ours', 'ourmethod', 'OurMethod', 'Model', 'MODEL',
        'Method', 'Theorem', 'Lemma', 'Corollary', 'Proposition',
        'Definition', 'Proof', 'Remark', 'Note', 'Example',
        'xmax', 'xmin', 'ymax', 'ymin', 'zmax', 'zmin'
    ]

    fixed_count = 0
    for macro in macros:
        # Pattern: macro followed by a character that is not space, {}, letter
        pattern = r'\\' + macro + r'([^\s{}A-Za-z])'
        matches = re.findall(pattern, content)
        if matches:
            fixed_count += len(matches)
        content = re.sub(pattern, r'\\' + macro + r'{}\1', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return fixed_count

def main():
    if len(sys.argv) > 1:
        tex_file = sys.argv[1]
        if not os.path.exists(tex_file):
            print(f"Error: File not found: {tex_file}")
            sys.exit(1)
        fixed = fix_macros_in_file(tex_file)
        print(f'Fixed {fixed} macro occurrences in {tex_file}')
    else:
        # Process all .tex files in current directory
        import glob
        tex_files = glob.glob('*.tex')
        total_fixed = 0
        for tex_file in tex_files:
            fixed = fix_macros_in_file(tex_file)
            if fixed > 0:
                print(f'Fixed {fixed} macro occurrences in {tex_file}')
                total_fixed += fixed
        if total_fixed == 0:
            print('No macro issues found.')
        else:
            print(f'Total: Fixed {total_fixed} macro occurrences across {len(tex_files)} files.')

if __name__ == '__main__':
    main()
