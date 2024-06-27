# python s_upload.py file_name --server server_name --chunk-size 200000 --threads 1

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import sys
import time

import requests

HOST_NAME_MAIN = "https://uwu-logs.xyz"
HOST_NAME_TEST = "http://localhost:4000"

def local_timezone_name():
    timezone = time.altzone if time.daylight else time.timezone
    offset = timezone // 3600
    return f"Etc/GMT{offset:+}"

def send_post(d):
    print("send_post", len(d["data"]), d["headers"])
    q = requests.post(d["url"], data=d["data"], headers=d["headers"])
    return (d["headers"]["X-Chunk"], q)

class Upload:
    def __init__(
        self,
        file_name: str,
        server: str=None,
        threads=None,
        chunk_size=None,
        test=False,
    ) -> None:
        self.file_name = file_name
        self.file_path = Path(file_name)
        if not self.file_path.is_file():
            raise FileNotFoundError
        if self.file_path == Path(__file__).resolve():
            raise ValueError("Must include logs file as last argument")

        self.server = server

        try:
            self.threads = int(threads)
        except (TypeError, ValueError):
            self.threads = 1
        try:
            self.chunk_size = int(chunk_size)
        except (TypeError, ValueError):
            self.chunk_size = 256*1024
        if self.chunk_size > 100*1024*1024:
            raise ValueError("Chunk size must not exceed 100 megabytes")

        self.upload_id = str(datetime.now().timestamp())

        self.host_name = HOST_NAME_MAIN
        if test:
            self.host_name = HOST_NAME_TEST

    def run(self):
        self.send_file()
        self.send_finish()

        for response_json in self.upload_progress():
            print(response_json)
    
    def send_file(self):        
        with ThreadPoolExecutor(self.threads) as t:
            responses = t.map(send_post, self._chunks_gen())

        for chunk_id, response in responses:
            print(f"{chunk_id:>4} | {response.status_code} | {response.content}")

        print(">>> Uploaded all chunks")

    def send_finish(self):
        headers = {
            "Content-Type": "application/json",
        }
        request_json = {
            "filename": self.file_path.name,
            "server": self.server,
            "timezone": local_timezone_name(),
            "chunks": self.chunks_amount(),
        }
        response = requests.post(
            f"{self.host_name}/upload",
            json=request_json,
            headers=headers,
        )
        print(f">>> Send finish {response.status_code} | {response.content}")

    def upload_progress(self):
        for _ in range(200):
            response = requests.get(f"{self.host_name}/upload_progress")
            if response.headers.get("Content-Type") != "application/json":
                break
            if response.status_code != 200:
                break
            
            response_json = response.json() or {}
            yield response_json
            
            if response_json.get("done") in [1, "1"]:
                break
            
            time.sleep(1)

    def chunks_amount(self):
        chunks, _mod = divmod(self.full_size(), self.chunk_size)
        if _mod:
            chunks += 1
        return chunks

    def full_size(self):
        return self.file_path.stat().st_size
    
    def _chunks_gen(self):
        max_chunks = self.chunks_amount()
        with open(self.file_path, "rb") as f:
            for chunk in range(max_chunks):
                file_slice = f.read(self.chunk_size)  
                if not file_slice:
                    break
                yield {
                    "url": f"{self.host_name}/upload",
                    "data": file_slice,
                    "headers": self._headers(chunk),
                }

    def _headers(self, chunk):
        return  {
            "X-Chunk": str(chunk),
            "X-Upload-ID": self.upload_id,
        }


def argv_get_server(flags: list[str]):
    for flag in ["-s", "--server"]:
        try:
            i = flags.index(flag) + 1
            return flags[i]
        except IndexError:
            print(f"{flag} flag must be paired with a server name")
            return
        except ValueError:
            pass

def argv_get_chunk_size(flags: list[str]):
    for flag in ["-c", "--chunk-size"]:
        try:
            i = flags.index(flag) + 1
            return flags[i]
        except IndexError:
            print(f"{flag} flag must be paired with a chunk size in bytes")
            return
        except ValueError:
            pass

def argv_get_threads(flags: list[str]):
    for flag in ["-t", "--threads"]:
        try:
            i = flags.index(flag) + 1
            return flags[i]
        except IndexError:
            print(f"{flag} flag must be paired with threads amount")
            return
        except ValueError:
            pass

def argv_upload_file_name(flags: list[str]):
    for flag in flags[1:]:
        p = Path(flag)
        if p.is_file():
            return flag

    raise ValueError("Must include logs file name")

def main():
    file_name = argv_upload_file_name(sys.argv)
    server = argv_get_server(sys.argv)
    threads = argv_get_threads(sys.argv)
    chunk_size = argv_get_chunk_size(sys.argv)
    upload = Upload(
        file_name,
        server=server,
        threads=threads,
        chunk_size=chunk_size,
    )
    upload.run()

def _test1():
    file_name = r"F:\wow-3.3.5a-HD\Logs\logs_cache\24-05-14--21-17--Meownya--Lordaeron.7z"
    upload = Upload(file_name, threads=16, test=1)
    upload.run()

if __name__ == "__main__":
    main()
