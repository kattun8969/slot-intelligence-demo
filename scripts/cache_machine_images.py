"""Cache explicitly approved, source-attributed machine/hint images inside docs/.

Run this as a branch-only GitHub Action. Do not scrape pages, bypass login/403,
or treat unknown images as belonging to another machine.
"""
from __future__ import annotations
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import urllib.request

from PIL import Image, UnidentifiedImageError

ROOT=Path(__file__).resolve().parents[1]
IMAGE_DIR=ROOT/"docs"/"assets"
MANIFEST=ROOT/"docs"/"machine-image-sources.json"
MAX_BYTES=8_000_000
HEADERS={"User-Agent":"SlotIntelligenceAssetCache/1.0 (attributed site images; source URL in manifest)"}


def cache_one(entry):
    url=entry["url"]
    dest=IMAGE_DIR/entry["path"]
    dest.parent.mkdir(parents=True,exist_ok=True)
    request=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(request,timeout=18) as response:
        if response.status!=200:
            raise ValueError("HTTP "+str(response.status))
        content_type=response.headers.get("Content-Type","")
        if not content_type.lower().startswith("image/"):
            raise ValueError("not an image content type")
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError("image too large")
    try:
        with Image.open(BytesIO(raw)) as img:
            img.load()
            if min(img.size)<130:
                raise ValueError("image unexpectedly small")
            img.thumbnail((740,900))
            img=img.convert("RGB")
            img.save(dest,"WEBP",quality=82,method=5)
    except (UnidentifiedImageError,OSError) as exc:
        raise ValueError("decode failed") from exc
    return {"id":entry["id"],"path":entry["path"],"bytes":dest.stat().st_size,"ok":True}


def main():
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema")!=1:
        raise SystemExit("unsupported manifest")
    report=[]
    for entry in data["images"]:
        if not entry["url"].startswith("https://"):
            raise ValueError("non HTTPS image")
        if not entry["path"].startswith(("machines/","hints/")) or not entry["path"].endswith(".webp"):
            raise ValueError("unsafe output path")
        try:
            result=cache_one(entry)
            print("cached",result["id"],result["bytes"])
            report.append(result)
        except Exception as exc:
            print("unavailable",entry["id"],type(exc).__name__,str(exc)[:160])
            report.append({"id":entry["id"],"path":entry["path"],"ok":False,"issue":type(exc).__name__})
    IMAGE_DIR.mkdir(parents=True,exist_ok=True)
    (IMAGE_DIR/"image-cache-report.json").write_text(json.dumps({
        "schema":1,"checked_at":datetime.now(timezone.utc).isoformat(),"results":report
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    success=sum(x["ok"] for x in report)
    print(f"cached {success} of {len(report)} images")
    if success==0:raise SystemExit("no images could be cached; check source URLs")


if __name__=="__main__":
    main()
