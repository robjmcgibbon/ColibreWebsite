#! /usr/bin/python3

import argparse
import glob
import os
import shutil
import subprocess
import yaml
import rcssmin

import generate_publication_list
import generate_mass_functions
import generate_user_map


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


def make_sidebar(sections):
    """
    Create the sidebar with the given sections.
    """
    sidebar = templates["sidebar.html"]

    links = ""
    for i, section in enumerate(sections):
        if section == 'page_description':
            continue
        links += f'      <li class="nav-item"><a class="nav-link" href="#sec{i}">{section}</a></li>\n'

    return template_replace(sidebar, {"LINK_LIST": links})


def make_page(page, pages, templates):
    """
    Create the page with the given name.

    The page consists of the general page template in which a header, navigation
    bar, footer and actual page contents are substituted.
    """
    template = templates["page.html"]
    style_template = templates["style.html"]
    script_template = templates["script.html"]
    description_template = templates["description.html"]

    with open(f"src/pages/{page}", "r") as pfile:
        page_contents = pfile.read()

    page_out = str(template)

    # check if we have a page-specific header
    extra_header = ""
    if "css" in pages[page]:
        for script in pages[page]["css"]:
            extra_header += template_replace(style_template, {"STYLE_SRC": script})
    if "prescripts" in pages[page]:
        for script in pages[page]["prescripts"]:
            extra_header += template_replace(script_template, {"SCRIPT_SRC": script})
    if "description" in pages[page]:
        extra_header += template_replace(description_template, {"DESCRIPTION": pages[page]['description']})
    page_out = template_replace(page_out, {"EXTRA_HEADER": extra_header})

    title = "The COLIBRE project"
    if not pages[page]["title"] == "":
        title += " - " + pages[page]["title"]

    # The value of "sidebar" in page.yml should be the yaml file
    # to load to determine the different sections contained in the page
    sidebar = ""
    if "sidebar" in pages[page]:
        with open(f'src/{pages[page]["sidebar"]}.yml') as f:
            sections = yaml.safe_load(f)
        sidebar = make_sidebar(list(sections.keys()))

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

    # create the page
    with open(f"build/{os.path.basename(page)}", "w") as ofile:
        ofile.write(page_out)


def copy_assets():
    """
    Copy all contents of src/assets/ into build/, regardless of the file type
    or name.
    """
    shutil.copytree('src/assets', 'build/assets')

def copy_slider_images():
    """
    Copy the src/slider_images/ into build/. We create compressed versions (for the
    sliders themselves, so they can load quickly), but we also copy across the full
    versions (as we have a download link for them).
    """
    # Compress slider images
    for dirname in os.listdir("src/slider_images"):
        os.makedirs(f"build/slider_images/{dirname}", exist_ok=True)
    for input_image in sorted(glob.glob("src/slider_images/*/*")):
        output_image = input_image.replace('src', 'build', 1).replace('.png', '.jpg')
        cmd = f'convert "{input_image}" -resize 800x800 -gravity center -background white -extent 800x800 -quality 90 "{output_image}"'
        print(f'Compressing {output_image}')
        run_process(cmd)

    # Copy the full size images
    for asset in sorted(glob.glob("src/slider_images/*")):
        shutil.copytree(asset, f"build/hires_slider_images/{os.path.basename(asset)}")


def copy_styles():
    """
    Copy all contents of src/css/ into build/, and minify it along the way.
    """

    cmd = f"mkdir build/css"
    run_process(cmd)

    for css in sorted(glob.glob("src/css/*.css")):
        with open(css, "r") as ifile, open(
            f"build/css/{os.path.basename(css)}", "w"
        ) as ofile:
            ofile.write(rcssmin.cssmin(ifile.read()))

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


def clean_build(keep_sliders=False, keep_images=False, keep_videos=False):
    """
    Clean up a previous build.
    """
    if keep_sliders and os.path.exists('build/slider_images'):
        run_process("mv build/slider_images tmp_slider_images")
        run_process("mv build/hires_slider_images tmp_hires_slider_images")
    else:
        keep_sliders = False

    if keep_images and os.path.exists('build/images'):
        run_process("mv build/images tmp_images")
    else:
        keep_images = False

    if keep_videos and os.path.exists('build/videos'):
        run_process("mv build/videos tmp_videos")
    else:
        keep_videos = False

    run_process("rm -rf build; mkdir build")

    if keep_sliders:
        run_process("mv tmp_slider_images build/slider_images")
        run_process("mv tmp_hires_slider_images build/hires_slider_images")
        print('Using sliders from previous build')
    else:
        run_process("mkdir build/slider_images build/hires_slider_images")

    if keep_images:
        run_process("mv tmp_images build/images")
        print('Using images from previous build')
    else:
        run_process("mkdir build/images")

    if keep_videos:
        run_process("mv tmp_videos build/videos")
        print('Using videos from previous build')
    else:
        run_process("mkdir build/videos")

    return keep_sliders, keep_images, keep_videos



def create_thumbnail(img_id, img_src, create_media):
    """
    Create a thumbnail for the given image file.
    """
    cmd = f'convert src/images/{img_src} -resize 200x200 -gravity center -background none -extent 200x200 build/images/{img_id}_200.png'
    if create_media:
        run_process(cmd)
    return f"images/{img_id}_200.png"


def create_image(img_id, img_src, create_media):
    """
    Copy the given image from src/images/ to build/, and resize if it is larger
    than 800x800 pixels.
    """
    if create_media:
        cmd = f"cp src/images/{img_src} build/images/{img_id}_full.png"
        run_process(cmd)
        cmd = f"convert src/images/{img_src} -resize 768x800\\> build/images/{img_id}_800.png"
        run_process(cmd)
    return f"images/{img_id}_800.png"


def create_video_thumbnail(img_id, img_src, create_media):
    """
    Create a thumbnail for the given video file.
    """
    if create_media:
        # Extract the frame 10 seconds from the end of the video
        cmd = f"ffmpeg -hide_banner -loglevel error -sseof -10 -i src/videos/{img_src} -vf scale=200:-1 -frames:v 1 build/videos/{img_id}_200.png"
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


def create_video(img_id, img_src, img_src_nosound, create_media):
    """
    Copy the given video file from src/images/ to build/.
    We could maybe do some conversions if necessary, but that is too complex for
    now.
    """
    if create_media:
        shutil.copyfile(f"src/videos/{img_src}", f"build/videos/{img_id}.mp4")

    if img_src_nosound:
        if create_media:
            shutil.copyfile(f"src/videos/{img_src_nosound}", f"build/videos/{img_id}_nosound.mp4")
        return (f"videos/{img_id}.mp4", f"videos/{img_id}_nosound.mp4")
    return f"videos/{img_id}.mp4", ""


def make_gallery(templates, input_sections, gallery_name, create_media):
    """
    Create the gallery from the given gallery sections dictionary.

    If create_media=False then skip copying the images/videos across 
    """

    # load all templates
    gallery_template = templates[f"gallery.html"]
    section_template = templates["gallery_section.html"]
    image_card_template = templates["image_card.html"]
    video_card_template = templates["video_card.html"]

    # loop over sections
    # modals are saved in one block, regardless of their section
    sections = ""
    for sid, (title, objects) in enumerate(input_sections.items()):
        if title == 'page_description':
            continue
        # cards are grouped per section
        cards = ""
        # loop over this section's images/videos
        for id, (obj_src, value) in enumerate(objects.items()):
            err_msg = f'Gallery object {obj_src} does not exist'
            assert os.path.exists(f'src/{gallery_name}/{obj_src}'), err_msg
            # generate a unique name for this image/video
            # this name will be used for thumbnail and image/video file names
            # it will also be used to identify the corresponding modal and
            # should therefore be unique
            obj_id = f"SEC{sid}IMG{id}"
            # distinguish between images and videos
            if obj_src.endswith('.mp4'):
                obj_type = 'video'
                obj_cap = value["desc"]
                obj_src_nosound = value.get("name_nosound", "")
            elif obj_src.endswith('.png') or obj_src.endswith('.jpg'):
                obj_type = 'image'
                obj_cap = value
            else:
                raise NotImplementedError(f'Unable to determine obj_type of {obj_src}')

            if obj_type == "image":
                obj_src_orig = create_image(obj_id, obj_src, create_media)
                obj_src_thumb = create_thumbnail(obj_id, obj_src, create_media)

                cards += template_replace(
                    image_card_template,
                    {
                        "IMG_CAPTION": obj_cap,
                        "IMG_SRC": obj_src_thumb,
                        "IMG_TYPE": obj_type,
                        "ORIG_SRC": obj_src_orig,
                    },
                )
            else:
                obj_src_orig, obj_src_orig_nosound = create_video(obj_id, obj_src, obj_src_nosound, create_media)
                obj_src_thumb = create_video_thumbnail(obj_id, obj_src, create_media)

                cards += template_replace(
                    video_card_template,
                    {
                        "IMG_CAPTION": obj_cap,
                        "IMG_SRC": obj_src_thumb,
                        "IMG_TYPE": obj_type,
                        "ORIG_SRC": obj_src_orig,
                        "ORIG_SRC_NOSOUND": obj_src_orig_nosound,
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

    # save the html
    with open(f"src/pages/{gallery_name}.html", "w") as ofile:
        nice_name = {'images': 'Image', 'videos': 'Video'}[gallery_name]
        ofile.write(template_replace(gallery_template, {"PAGE_DESCRIPTION": input_sections.get('page_description', ''), "IMG_SECTIONS": sections, "GALLERY_NAME": nice_name}))


def make_sliders(templates, input_sections):
    """
    Create the gallery from the given image sections dictionary.

    """

    # Load all templates
    sliders_template = templates[f"sliders.html"]
    section_template = templates["slider_section.html"]
    button_template = templates["slider_button.html"]

    # Helper function for creating html buttons
    def button_option(img_type, selected=False, underscore=False):
        internal_img_type = img_type.replace(" ", "_")
        if underscore:
            internal_img_type = '_' + internal_img_type
        option = f'        <option value="{internal_img_type}"'
        if selected:
            option += ' selected'
        option += f'>{img_type}</option>\n'
        return option

    # Loop through each slider section
    sections = ""
    state = "const state = {\n"
    for i_section, (section_title, section_info) in enumerate(input_sections.items()):

        # Initialise a list of all images that the sliders require
        all_images = []

        buttons = ""
        left_img_path = f"slider_images/{section_info['dirname']}/L"
        right_img_path = f"slider_images/{section_info['dirname']}/R"

        # "show_left_right" detemines which values will show on left/right
        if section_info["show_Left_Right"]:
            # Adding button for left image
            button_values = ""
            img_type = section_info[section_info["show_Left_Right"]][0]
            button_values += button_option(img_type, selected=True)
            left_type = img_type.replace(" ", "_")
            for img_type in section_info[section_info["show_Left_Right"]][1:]:
                button_values += button_option(img_type)
                all_images.append(f'L{img_type.replace(" ", "_")}')
            buttons += template_replace(
                button_template,
                {
                    "BUTTON_TITLE": "Left image",
                    "BUTTON_VALUES": button_values,
                    "SLIDER_ID": str(i_section),
                    "JS_FUNCTION": "setLeftImage",
                },
            )
            left_img_path += left_type
            # Adding button for right image
            button_values = ""
            img_type = section_info[section_info["show_Left_Right"]][0]
            button_values += button_option(img_type)
            img_type = section_info[section_info["show_Left_Right"]][1]
            button_values += button_option(img_type, selected=True)
            right_type = img_type.replace(" ", "_")
            for img_type in section_info[section_info["show_Left_Right"]][2:]:
                button_values += button_option(img_type)
                all_images.append(f'R{img_type.replace(" ", "_")}')
            buttons += template_replace(
                button_template,
                {
                    "BUTTON_TITLE": "Right image",
                    "BUTTON_VALUES": button_values,
                    "SLIDER_ID": str(i_section),
                    "JS_FUNCTION": "setRightImage",
                },
            )
            right_img_path += right_type
        else:
            left_type = ''
            right_type = ''
            all_images.append('L')
            all_images.append('R')

        # Adding other buttons
        other_types = []
        for i_button, button_title in enumerate(section_info['buttons']):
            prev_all_images = all_images.copy()
            all_images = []
            button_values = ""
            img_type = section_info[button_title][0]
            left_img_path += '_' + img_type.replace(" ", "_")
            right_img_path += '_' + img_type.replace(" ", "_")
            other_types.append(img_type.replace(" ", "_"))
            button_values += button_option(img_type, selected=True, underscore=True)
            for img_type in section_info[button_title][1:]:
                button_values += button_option(img_type, underscore=True)
                for image_name in prev_all_images:
                    all_images.append(f'{image_name}_{img_type.replace(" ", "_")}')
            buttons += template_replace(
                button_template,
                {
                    "BUTTON_TITLE": button_title,
                    "BUTTON_VALUES": button_values,
                    "SLIDER_ID": str(i_section),
                    "JS_FUNCTION": f"setType{i_button}",
                },
            )

        # Add this section
        sections += template_replace(
            section_template,
            {
                "SECTION_TITLE": section_title,
                "DESCRIPTION": section_info['description'],
                "SLIDER_ID": str(i_section),
                "BUTTONS": buttons,
                "INITIAL_LEFT_IMG": left_img_path,
                "INITIAL_RIGHT_IMG": right_img_path,
            },
        )

        # Add the initial state of the image
        state += f"slider{i_section}: {{ "
        state += f"imageDirectory: '{section_info['dirname']}', "
        state += f"leftType: '{left_type}', "
        state += f"rightType: '{right_type}'"
        for i_type in range(5):
            img_type = "_" + other_types[i_type] if i_type < len(other_types) else ""
            state += f", type{i_type}: '{img_type}'"
        state += " },\n"

        # Loop through all possible images and assert that they exist
        for image_name in all_images:
            image_path = f'src/slider_images/{section_info["dirname"]}/{image_name}.png'
            assert os.path.exists(image_path), f'{image_path} is used by sliders, but does not exist'

    state += "};"

    sliders = template_replace(
        sliders_template,
        {
            "SECTIONS": sections,
            "STATE": state,
        },
    )

    # generate the new src/pages/gallery.html
    with open(f"src/pages/sliders.html", "w") as ofile:
        ofile.write(sliders)



if __name__ == "__main__":
    """
    Main script body. Takes no input arguments.
    """

    # Load the html templates
    templates = load_templates()

    # Check if we just want a minor update
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update papers and team map',
    )
    args = parser.parse_args()
    if args.update:
        generate_publication_list.generate_publication_list(skip_query=False)
        with open("src/pages.yml", "r") as handle:
            pages = yaml.safe_load(handle)
        for page in ['papers.html']:
            make_page(page, pages, templates)
        generate_user_map.generate_user_map()
        exit()

    # Whether to skip build steps to allow for a quick website build
    keep_sliders = False
    keep_images = False
    keep_videos = False
    skip_ads_query = False

    # Clean up any existing build, create new build directories
    keep_sliders, keep_images, keep_videos = clean_build(
        keep_sliders=keep_sliders,
        keep_images=keep_images,
        keep_videos=keep_videos,
    )

    # Generate the images gallery
    with open("src/images.yml", "r") as handle:
        images = yaml.safe_load(handle)
    make_gallery(templates, images, 'images', not keep_images)

    # Generate the video gallery
    with open("src/videos.yml", "r") as handle:
        videos = yaml.safe_load(handle)
    make_gallery(templates, videos, 'videos', not keep_videos)

    # Create the sliders
    with open("src/sliders.yml", "r") as handle:
        sliders = yaml.safe_load(handle)
    make_sliders(templates, sliders)

    # Generate a list of publications
    if skip_ads_query:
        print('Not querying ADS for analysis papers')
    generate_publication_list.generate_publication_list(skip_query=skip_ads_query)

    # Generate the map of colibre users
    generate_user_map.generate_user_map()

    # Generate the simulation mass functions
    generate_mass_functions.generate_mass_functions()

    # Now generate all the pages.
    with open("src/pages.yml", "r") as handle:
        pages = yaml.safe_load(handle)
    for page in pages:
        make_page(page, pages, templates)

    # Copy the assets.
    copy_assets()
    copy_styles()
    if not keep_sliders:
        copy_slider_images()
