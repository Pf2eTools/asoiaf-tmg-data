from fpdf import FPDF
from song_data import *
from PIL import Image, ImageOps
from math import ceil

SIZE_SMALL = {
    "w": 64,
    "h": 90,
}
SIZE_LARGE = {
    "w": 120,
    "h": 70,
}


def get_real_size_mm(entity):
    if isinstance(entity, SongDataSpecials):
        if entity.size is not None:
            return entity.size
    elif isinstance(entity, SongDataUnit):
        return SIZE_LARGE

    return SIZE_SMALL


def get_images(entity: SongEntity, meta: SongMeta):
    author = meta.author
    if author == "CMON":
        lang = meta.language
        faction = entity.faction
        path = f"./generated/{lang}/{faction}/{entity.id}.jpg"
        back_path = f"./generated/{lang}/{faction}/{entity.id}b.jpg"
    else:
        raise Exception(f"Unimplemented")

    img = Image.open(path)
    try:
        back_img = Image.open(back_path)
    except FileNotFoundError:
        back_img = None

    return img, back_img


def apply_print_margin(img: Image, im_size_mm, margin_mm):
    px_per_mm = img.width / im_size_mm["w"]
    margin_px = ceil(margin_mm * px_per_mm)
    out = Image.new("RGB", (img.width + 2 * margin_px, img.height + 2 * margin_px))

    flipped = ImageOps.flip(img)
    mirrored = ImageOps.mirror(img)
    flipped_mirrored = ImageOps.flip(mirrored)

    out.paste(img, (margin_px, margin_px))
    out.paste(mirrored, (margin_px - img.width, margin_px))
    out.paste(mirrored, (margin_px + img.width, margin_px))
    out.paste(flipped, (margin_px, margin_px - img.height))
    out.paste(flipped, (margin_px, margin_px + img.height))

    out.paste(flipped_mirrored, (margin_px + img.width, margin_px + img.height))
    out.paste(flipped_mirrored, (margin_px + img.width, margin_px - img.height))
    out.paste(flipped_mirrored, (margin_px - img.width, margin_px + img.height))
    out.paste(flipped_mirrored, (margin_px - img.width, margin_px - img.height))

    return out


def create_print_pdf(entities: [SongEntity], meta: SongMeta, margin_mm):
    pdf = FPDF()
    pdf.set_image_filter("DCTDecode")

    for entity in entities:
        img, back = get_images(entity, meta)
        size = get_real_size_mm(entity)
        printable_img = apply_print_margin(img, size, margin_mm)
        w_pdf, h_pdf = size["w"] + 2 * margin_mm, size["h"] + 2 * margin_mm

        addcount = 2
        if entity.role == "ncu":
            addcount = 1
        elif entity.role in ["unit", "attachment"] and entity.character:
            addcount = 1
        elif isinstance(entity, SongDataSpecials) and not entity.id == "50201": # crannog poison
            addcount = 1

        for _ in range(addcount):
            pdf.add_page(format=(w_pdf, h_pdf))
            pdf.image(printable_img, x=0, y=0, w=w_pdf, h=h_pdf)
            if back is not None:
                printable_back_img = apply_print_margin(back, size, margin_mm)
                pdf.add_page(format=(w_pdf, h_pdf))
                pdf.image(printable_back_img, x=0, y=0, w=w_pdf, h=h_pdf)

    return pdf


def main():
    for lang in ["en", "de"]:
        for version in ["s07", "all"]:
            for size in ["lg", "small"]:
                for faction in FACTIONS:
                    faction_data = DataLoader.load_structured(f"./data/{lang}/{faction}.json")
                    if version == "all":
                        pdf_data = faction_data.all_entities
                    else:
                        pdf_data = [e for e in faction_data.all_entities if e.version.lower() == version]
                    if size == "lg":
                        pdf_data = [e for e in pdf_data if get_real_size_mm(e) == SIZE_LARGE]
                    elif size == "small":
                        pdf_data = [e for e in pdf_data if get_real_size_mm(e) == SIZE_SMALL]

                    pdf = create_print_pdf(pdf_data, faction_data.meta, 1)
                    savepath = f"./pdf/{lang}-{faction}-{version}-{size}.pdf"
                    print(f"Saving to {savepath}...")
                    pdf.output(savepath)


if __name__ == '__main__':
    main()
