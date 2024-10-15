#! /usr/bin/python3

import glob
import os
import shutil
import subprocess
import yaml
import jsmin
import htmlmin
import rcssmin
import json


def load_templates():
    """
    Load all the .html templates in the template folder.
    """
    templates = {}
    for template in sorted(glob.glob("src/templates/*.html")):
        with open(template, "r") as tfile:
            templates[os.path.basename(template)] = tfile.read()

    return templates


def template_replace(input_string, substitutes):
    """
    Return a copy of the given input string with all replacements made that are
    specified in the substitutes directory.

    E.g.
      {"A": "a"}
    will replace all occurrences of "%A%" in input_string with "a".
    """
    output_string = str(input_string)
    for key, val in substitutes.items():
        output_string = output_string.replace(f"%{key}%", val)
    return output_string


def make_navbar(pages, templates):
    """
    Create the navigation bar with the given pages.
    """
    navlink = templates["navlink.html"]
    navbar = templates["navbar.html"]

    links = ""
    for page in pages:
        # skip pages with no name
        if not pages[page]["title"] == "":
            links += template_replace(
                navlink, {"HREF": page, "NAME": pages[page]["title"]}
            )

    return template_replace(navbar, {"LINK_LIST": links})


def make_sidebar(content, templates, page, obj_type):
    """
    Create the sidebar with the given lightcones/slider images.
    """
    sidebarlink = templates["sidebarlink.html"]
    sidebar = templates["sidebar.html"]

    links = ""
    if obj_type == "lightcones":
        for c in content:
            if c == page:
                links += template_replace(
                    sidebarlink, {"HREF": c, "ACTIVE": "active", "NAME": content[c]["linktitle"]}
                )
            else:
                links += template_replace(
                    sidebarlink, {"HREF": c, "ACTIVE": "", "NAME": content[c]["linktitle"]}
                )
    elif obj_type == "images":
        for i,c in enumerate(content["sliders"]):
            prop = "\" id=\"link" + str(i)
            if i == 0:
                prop = "active" + prop
            links += template_replace(
                sidebarlink, {"HREF": "#\" onClick=\"selectSlider(" + str(i) + ")\"", 
                              "ACTIVE": prop, "NAME": c["linkname"]}
            )
    elif obj_type == "videos":
        for i,c in enumerate(content):
            links += template_replace(
                sidebarlink, {"HREF": "#sec" + str(i), "ACTIVE": "", "NAME" : c}
            )

    return template_replace(sidebar, {"LINK_LIST": links})


def make_page(page, pages, templates, lightcones):
    """
    Create the page with the given name.

    The page consists of the general page template in which a header, navigation
    bar, footer and actual page contents are substituted.
    """
    template = templates["page.html"]
    style_template = templates["style.html"]
    script_template = templates["script.html"]

    with open(f"src/pages/{page}", "r") as pfile:
        page_contents = pfile.read()

    page_out = str(template)

    # check if we have a page-specific header
    extra_header = ""
    if "style" in pages[page]:
        for script in pages[page]["style"]:
            extra_header += template_replace(style_template, {"STYLE_SRC": script})
    if "prescripts" in pages[page]:
        for script in pages[page]["prescripts"]:
            extra_header += template_replace(script_template, {"SCRIPT_SRC": script})
    page_out = template_replace(page_out, {"EXTRA_HEADER": extra_header})

    # check if we have a page-specific footer
    extra_footer = ""
    if "postscripts" in pages[page]:
        for script in pages[page]["postscripts"]:
            extra_footer += template_replace(script_template, {"SCRIPT_SRC": script})
    page_out = template_replace(page_out, {"EXTRA_FOOTER": extra_footer})

    title = "The FLAMINGO project"
    if not pages[page]["title"] == "":
        title += " - " + pages[page]["title"]

    sidebar = ""
    if "sidebar" in pages[page]:
        if pages[page]["sidebar"] == "lightcones":
            sidebar = make_sidebar(lightcones, templates, page, "lightcones")
        elif pages[page]["sidebar"] == "images":
            with open("src/assets/images.json",'r') as f:
                imagedata=json.load(f)
            sidebar = make_sidebar(imagedata, templates, page, "images")
        elif pages[page]["sidebar"] == "videos":
            with open("src/videos.yml", "r") as f:
                videos = yaml.safe_load(f)
            sidebar = make_sidebar(videos, templates, page, "videos")

    # now add the actual page contents
    page_out = template_replace(
        page_out,
        {
            "PAGE_TITLE": title,
            "NAVBAR": make_navbar(pages, templates),
            "PAGE_CONTENTS": page_contents,
            "SIDEBAR": sidebar,
        },
    )

    # make slimmer
    page_out = htmlmin.minify(page_out, remove_comments=True, remove_empty_space=True)

    # create the page
    with open(f"build/{os.path.basename(page)}", "w") as ofile:
        ofile.write(page_out)


def copy_assets():
    """
    Copy all contents of src/assets/ into build/, regardless of the file type
    or name.
    """
    for asset in sorted(glob.glob("src/assets/*")):
        shutil.copyfile(asset, f"build/assets/{os.path.basename(asset)}")
    for asset in sorted(glob.glob("src/lightconedata/*")):
        shutil.copyfile(asset, f"build/lightconedata/{os.path.basename(asset)}")


def copy_slider_images():
    """
    Copy all contents of src/slider_images/ into build/, regardless of the file type
    or name.
    """
    for asset in sorted(glob.glob("src/slider_images/*")):
        shutil.copyfile(asset, f"build/slider_images/{os.path.basename(asset)}")


def copy_styles():
    """
    Copy all contents of src/css/ into build/, and minify it along the way.
    """
    for css in sorted(glob.glob("src/css/*.css")):
        with open(css, "r") as ifile, open(
            f"build/css/{os.path.basename(css)}", "w"
        ) as ofile:
            ofile.write(rcssmin.cssmin(ifile.read()))


def copy_scripts():
    """
    Copy all contents of src/javascript/ into build/, and minify it along the
    way.
    """
    for script in sorted(glob.glob("src/javascript/*.js")):
        with open(script, "r") as ifile, open(
            f"build/js/{os.path.basename(script)}", "w"
        ) as ofile:
            ofile.write(jsmin.jsmin(ifile.read()))


def run_process(command, return_output=False):
    """
    Safely run a command using subprocess.
    """
    if return_output:
      status = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
      if status.returncode != 0:
        raise RuntimeError(f'Error running command "{command}"!')
      return status.stdout.decode("utf-8")
    else:
      status = subprocess.run(command, shell=True)
      if status.returncode != 0:
        raise RuntimeError(f'Error running command "{command}"!')


def clean_build():
    """
    Clean up a previous build.
    """
    cmd = f"rm -rf build/*"
    run_process(cmd)
    cmd = f"mkdir -p build/assets build/css build/images build/js build/lightconedata build/slider_images build/videos"
    run_process(cmd)


def create_thumbnail(img_id, img_src):
    """
    Create a thumbnail for the given image file.
    """
    cmd = f"magick src/images/{img_src} -resize 200x200 build/images/{img_id}_200.png"
    run_process(cmd)
    return f"images/{img_id}_200.png"


def create_image(img_id, img_src):
    """
    Copy the given image from src/images/ to build/, and resize if it is larger
    than 800x800 pixels.
    """
#    file_name, file_extension = os.path.splitext(f"{img_src}")
#    if file_extension == ".pdf":
#        cmd = f"magick -density 600 src/images/{img_src} -quality 100 -flatten src/images/{file_name}.png"
#        run_process(cmd)
#        img_src = file_name + ".png"
    cmd = f"cp src/images/{img_src} build/images/{img_id}_full.png"
    run_process(cmd)
    cmd = f"magick src/images/{img_src} -resize 768x800\> build/images/{img_id}_800.png"
    run_process(cmd)
    return f"images/{img_id}_800.png"


def create_video_thumbnail(img_id, img_src):
    """
    Create a thumbnail for the given video file.
    """
    ## first, extract the first frame from the video
    #cmd = f"ffmpeg -hide_banner -loglevel error -i src/videos/{img_src} -vframes 1 -r 1 -vf scale=200:-1 -f image2 build/videos/{img_id}_200.png"
    # now the last frame is used instead, as it's generally more interesting
    cmd = f"ffmpeg -hide_banner -loglevel error -sseof -1 -i src/videos/{img_src} -vsync 0 -q:v 1 -update true -vf scale=200:-1 -f image2 build/videos/{img_id}_200.png"
    run_process(cmd)
    # get the dimensions of the first frame (width is fixed, but height is variable)
    cmd = f"identify build/videos/{img_id}_200.png"
    output = run_process(cmd, return_output=True)
    dim = output.split()[2].split("x")
    w = int(dim[0])
    h = int(dim[1])
    if not w == 200:
        raise RuntimeError(f"Wrong thumbnail width: {w}x{h}!")
    # now draw a circle and arrow (poor man's play icon) on top of it
    cmd = f'mogrify -gravity Center -draw "fill none stroke rgba(255,255,255,0.5) stroke-linecap round stroke-width 2 circle {w//2},{h//2} {w//2},{h//2+20}" -draw "fill rgba(255,255,255,0.5) stroke-linecap round path \'M {w//2-5},{h//2-10} L {w//2-5},{h//2+10} L {w//2+10},{h//2} Z\'" build/videos/{img_id}_200.png'
    run_process(cmd)
    #Additionally crop images
    cmd = f"mogrify -gravity center -extent 200x100 build/videos/{img_id}_200.png"
    run_process(cmd)
    return f"videos/{img_id}_200.png"


def create_video(img_id, img_src):
    """
    Copy the given video file from src/images/ to build/.
    We could maybe do some conversions if necessary, but that is too complex for
    now.
    """
    shutil.copyfile(f"src/videos/{img_src}", f"build/videos/{img_id}.mp4")
    return f"videos/{img_id}.mp4"


def make_gallery(templates, input_sections, obj_type):
    """
    Create the gallery from the given image sections dictionary.

    The dictionary should have the following structure:
      {"SECTION HEADING": {"img.png": "Caption", "video.mp4": "Caption},
       "SECTION HEADING": {"img.png": "Caption"}}
    Only ".png" and ".mp4" are supported, for respectively images and videos.
    All ".png/mp4" files listed should be present in src/images/.
    """

    # load all templates
    gallery_template = templates[f"{obj_type}_gallery.html"]
    section_template = templates["gallery_section.html"]
    card_template = templates["image_card.html"]

    # loop over sections
    # modals are saved in one block, regardless of their section
    sections = ""
    for sid, (title, objects) in enumerate(input_sections.items()):
        # cards are grouped per section
        cards = ""
        # loop over this section's images/videos
        for id, (obj_src, obj_cap) in enumerate(objects.items()):
            # generate a unique name for this image/video
            # this name will be used for thumbnail and image/video file names
            # it will also be used to identify the corresponding modal and
            # should therefore be unique
            obj_id = f"SEC{sid}IMG{id}"
            # distinguish between images (.png) and videos (anything else)
            if obj_type == "image":
                obj_src_orig = create_image(obj_id, obj_src)
                obj_src_thumb = create_thumbnail(obj_id, obj_src)
            else:
                obj_src_orig = create_video(obj_id, obj_src)
                obj_src_thumb = create_video_thumbnail(obj_id, obj_src)
            cards += template_replace(
                card_template,
                {
                    "IMG_CAPTION": obj_cap,
                    "IMG_SRC": obj_src_thumb,
                    "IMG_TYPE": obj_type,
                    "ORIG_SRC": obj_src_orig,
                },
            )
        if obj_type != "video":
            sections += template_replace(
                section_template, {"SECTION_TITLE": title, "SECTION_ID": "sec" + str(sid),
                                    "IMG_CARDS": cards}
        )
        else:
            sections += template_replace(
                section_template, {"SECTION_TITLE": title, "SECTION_ID": "sec" + str(sid) + 
                                   "\" style=\"padding-top: 86px; margin-top: -76px;",
                                    "IMG_CARDS": cards}
        )

    # generate the new src/pages/gallery.html
    with open(f"src/pages/{obj_type}_gallery.html", "w") as ofile:
        ofile.write(template_replace(gallery_template, {"IMG_SECTIONS": sections}))


def make_lightcone_slider(lightcones, lightcone, templates):
    """
    Create a lightcone slider from the given lightcone dictionary.
    """

    # load the template
    template = templates["lightcone_slider.html"]

    # generate the new src/pages/lightcone_XX.html
    with open(f"src/pages/{lightcone}", "w") as ofile:
        ofile.write(template_replace(template, {
            "QUANTITYSHORT": lightcones[lightcone]["shortname"],
            "QUANTITYFULL": lightcones[lightcone]["fullname"],
            "RANGE_TEXT": lightcones[lightcone]["rangetext"],
        },
        ))


if __name__ == "__main__":
    """
    Main script body. Takes no input arguments (for now).
    """

    with open("src/pages.yml", "r") as handle:
        pages = yaml.safe_load(handle)

    with open("src/images.yml", "r") as handle:
        images = yaml.safe_load(handle)

    with open("src/videos.yml", "r") as handle:
        videos = yaml.safe_load(handle)

    with open("src/lightcones.yml", "r") as handle:
        lightcones = yaml.safe_load(handle)

    # Clean up a previous build, if it exists.
    clean_build()
    # Load the templates.
    templates = load_templates()
    # First, generate the galleries.
    make_gallery(templates, videos, "video")
    make_gallery(templates, images, "image")
    # Now prepare the light cones.
    for lightcone in lightcones:
        make_lightcone_slider(lightcones, lightcone, templates)
    # Now generate all the pages.
    for page in pages:
        make_page(page, pages, templates, lightcones)
    # Copy the assets.
    copy_assets()
    copy_styles()
    copy_scripts()
    copy_slider_images()
