import sys
from pathlib import Path

# python3 cifrar.py <arquivo> [n] [k]   (padrão: 3 partes, 2 abrem)

if len(sys.argv) < 2:
    sys.exit("uso: python3 cifrar.py <arquivo> [n] [k]")

original = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
if not 1 <= k <= n:
    sys.exit("k precisa estar entre 1 e n")
