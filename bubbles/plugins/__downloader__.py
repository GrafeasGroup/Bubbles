import re
from mimetypes import guess_extension
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests


class PictureDownloader:
    filename_finder = re.compile(r"filename=(?P<quote>[\"']?)(?P<filename>[^\"']+)(?P=quote);?", re.IGNORECASE)

    suffix_transform = {
        'gif': re.compile(r'\.?gif$'),
        'jpg': re.compile(r'\.?jpe?g$'),
        'png': re.compile(r'\.?png$'),
    }

    def normalize_suffix(self, suffix: str) -> str:
        for normal_suffix in self.suffix_transform.keys():
            if self.suffix_transform[normal_suffix].findall(suffix):
                return normal_suffix

        raise ValueError

    def suffix_from_content_type(self, resp: requests.Response) -> str:
        suffix = guess_extension(resp.headers['Content-Type'].split(';')[0].strip())
        if not suffix:
            raise ValueError

        return self.normalize_suffix(suffix)

    def suffix_from_content_disposition(self, resp: requests.Response) -> str:
        if 'Content-Disposition' not in resp.headers.keys():
            raise ValueError

        m = self.filename_finder.match(resp.headers['Content-Disposition'])
        if not m:
            raise ValueError

        return self.normalize_suffix(
            Path(m.group('filename')).suffix
        )

    def download_pic(self, pic_url: str) -> Path:
        resp = requests.get(pic_url, stream=True, timeout=30)  # 30 second timeout

        try:
            suffix = self.suffix_from_content_disposition(resp)
        except ValueError:
            suffix = self.suffix_from_content_type(resp)

        # Get file suffix
        with NamedTemporaryFile(mode='wb', suffix=f".{suffix}", delete=False) as f:
            filename = Path(f.name)
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

        return filename
    pass

