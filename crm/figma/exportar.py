"""Converte o PNG do get_screenshot do Figma (maxDimension 1350, enableBase64Response true) no JPG do post.
O Claude Code salva a imagem em ~/.claude/projects/.../tool-results/mcp-Figma-blob-*.png (o caminho aparece na resposta).
Uso: python3 crm/figma/exportar.py <png> crm/postados-img/AAAA-MM-DD-p1.jpg"""
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
if im.size != (1080, 1350):
    if abs(im.width / im.height - 0.8) > 0.01:
        sys.exit(f'tamanho inesperado {im.size}: confira o nodeId e use maxDimension 1350')
    im = im.resize((1080, 1350), Image.LANCZOS)
im.save(dst, quality=93)
print('ok', dst, im.size)
