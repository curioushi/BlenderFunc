import requests
import os

headers = {
    'User-Agent': 'Mozilla/5.0'
}

hdr_names = []
with open('scripts/hdr_infos.txt', 'r') as f:
    for line in f:
        hdr_names.append(line.strip())

output_dir = 'resources/hdr'
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

for i, name in enumerate(hdr_names):
    url = 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/{}_4k.hdr'.format(name)
    filepath = os.path.join(output_dir, '{}.hdr'.format(name))
    print('{}/{}: {}'.format(i + 1, len(hdr_names), name))
    if os.path.exists(filepath):
        continue
    try:
        request = requests.get(url, headers=headers)
        with open(filepath, 'wb') as file:
            file.write(request.content)
    except:
        pass
