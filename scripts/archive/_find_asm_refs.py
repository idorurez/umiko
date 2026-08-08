"""Find SLDPRT filename references embedded in binary .SLDASM files.

SolidWorks assemblies are OLE compound documents. Component filename
references live in specific streams (e.g., 'DocumentSummaryInformation',
'ThirdPtyStore', and the assembly's own reference table). Try olefile
first; fall back to broad UTF-16LE / ASCII text scans if a stream isn't
where we expect it.
"""
import os
import re
import olefile


def find_sldprt_refs(path):
    refs = set()
    if not olefile.isOleFile(path):
        return refs

    ole = olefile.OleFileIO(path)
    for stream_name in ole.listdir():
        stream_path = '/'.join(stream_name)
        try:
            data = ole.openstream(stream_name).read()
        except Exception:
            continue
        # Try UTF-16LE decode + regex
        try:
            text = data.decode('utf-16-le', errors='ignore')
            for m in re.finditer(r'([A-Za-z0-9_.\-\\/ ^~]{1,120}\.SLDPRT)',
                                 text, re.IGNORECASE):
                fn = m.group(1).replace('/', os.sep).split(os.sep)[-1].strip()
                if fn.upper().endswith('.SLDPRT'):
                    refs.add(fn)
        except Exception:
            pass
        # Latin-1 (byte-preserving) decode + regex — catches ASCII paths
        try:
            text = data.decode('latin-1', errors='ignore')
            for m in re.finditer(r'([A-Za-z0-9_.\-\\/ ^~]{1,120}\.SLDPRT)',
                                 text, re.IGNORECASE):
                fn = m.group(1).replace('/', os.sep).split(os.sep)[-1].strip()
                if fn.upper().endswith('.SLDPRT'):
                    refs.add(fn)
        except Exception:
            pass
    ole.close()
    return refs


asms_to_scan = []
for f in os.listdir('cad'):
    if f.endswith('.SLDASM') and not f.startswith('~$'):
        asms_to_scan.append(os.path.join('cad', f))

print(f'Scanning {len(asms_to_scan)} SLDASM files for SLDPRT references...\n')

all_refs = set()
for asm in asms_to_scan:
    refs = find_sldprt_refs(asm)
    if refs:
        print(f'{os.path.basename(asm)}: {len(refs)} refs')
        all_refs |= refs

print(f'\nTotal unique SLDPRT filenames referenced: {len(all_refs)}')
print('\nReferenced:')
for r in sorted(all_refs)[:40]:
    print(f'  {r}')
if len(all_refs) > 40:
    print(f'  ... {len(all_refs)-40} more')

# On disk
on_disk = {f for f in os.listdir('cad')
           if f.endswith('.SLDPRT') and not f.startswith('~$')}
unreferenced = on_disk - all_refs

print(f'\nOn disk: {len(on_disk)}, referenced: {len(all_refs & on_disk)}, unreferenced: {len(unreferenced)}')

with open('scripts/_unreferenced_sldprts.txt', 'w', encoding='utf-8') as f:
    for name in sorted(unreferenced):
        f.write(name + '\n')
print(f'\nWrote {len(unreferenced)} names to scripts/_unreferenced_sldprts.txt')
