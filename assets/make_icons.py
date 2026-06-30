from PIL import Image, ImageDraw, Image
import struct, os

OUT = os.path.join(os.path.dirname(__file__))

im = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

d.rounded_rectangle((32, 32, 992, 992), radius=200, fill="#007aff")

d.rounded_rectangle((160, 260, 860, 760), radius=60, fill="#ffffff")

d.line((240, 420, 780, 420), fill="#007aff", width=18)
d.line((240, 540, 640, 540), fill="#007aff", width=18)
d.line((240, 660, 520, 660), fill="#007aff", width=18)

im.save(os.path.join(OUT, "icon.png"))

sizes_ico = [16, 32, 48, 64, 128, 256]
imgs = [im.resize((w, w)) for w in sizes_ico]


def make_ico(images, out_path):
    import struct
    entries = []
    offset = 6 + 16 * len(images)
    for img in images:
        w, h = img.size
        w8 = 0 if w >= 256 else w
        h8 = 0 if h >= 256 else h
        raw = img.tobytes("raw", "BGRA")
        and_mask = Image.new("1", (w, h), 0)
        mask_bytes = and_mask.tobytes("raw", "1")
        mask_len = (w * 4 + 31) // 32 * 4 * h
        mask_bytes += b"\x00" * (mask_len - len(mask_bytes))
        total = len(raw) + len(mask_bytes)
        entries.append((w8, h8, total, offset, raw + mask_bytes))
        offset += total
    with open(out_path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(images)))
        for w, h, total, off, _ in entries:
            f.write(struct.pack("<BBHHII", w, h, 0, 1, 32, total, off))
        for _, _, _, _, payload in entries:
            f.write(payload)


make_ico(imgs, os.path.join(OUT, "icon.ico"))

sizes_iconset = [16, 32, 64, 128, 256, 512, 1024]
iconset = os.path.join(OUT, "icon.iconset")
os.makedirs(iconset, exist_ok=True)
for w in sizes_iconset:
    img = im.resize((w, w))
    img.save(os.path.join(iconset, f"icon_{w}x{w}.png"))
    img2 = im.resize((w * 2, w * 2))
    img2.save(os.path.join(iconset, f"icon_{w}x{w}@2x.png"))

print("OK: icon.png, icon.ico, icon.iconset/")
