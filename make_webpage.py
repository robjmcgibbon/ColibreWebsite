#! /usr/bin/python3

import argparse
import glob
import json
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
        if pages[page]["title"] == "":
            continue

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
        if section in ['page_description', 'title']:
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

def copy_paper_data():
    if os.path.exists('src/paper_data'):
        shutil.copytree('src/paper_data', 'build/paper_data')

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
        # Subdirectories are created lazily by copy_video_file/make_video_poster.
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


def copy_video_file(dirname, filename, create_media, required=True):
    """
    Copy a video file from src/videos/[dirname/]filename to the equivalent
    location under build/.
    """
    src_dir = f"src/videos/{dirname}" if dirname else "src/videos"
    build_dir = f"build/videos/{dirname}" if dirname else "build/videos"
    src_path = f"{src_dir}/{filename}"
    exists = os.path.exists(src_path)
    if required:
        assert exists, f"{src_path} is used by the videos page but does not exist"
    elif not exists:
        return ""
    if create_media:
        os.makedirs(build_dir, exist_ok=True)
        shutil.copyfile(src_path, f"{build_dir}/{filename}")
    return f"videos/{dirname}/{filename}" if dirname else f"videos/{filename}"


def make_video_poster(dirname, filename, create_media):
    """
    Create a poster thumbnail (a JPEG frame grab, downscaled to at most 960px
    wide, for use as a <video poster>) for the given video file, taken 10
    seconds from the end. Downscaled + JPEG rather than a full-resolution PNG
    since the poster is fetched over the network on every axis change
    """
    video_name = filename.replace('.mp4', '')
    src_dir = f"src/videos/{dirname}" if dirname else "src/videos"
    build_dir = f"build/videos/{dirname}" if dirname else "build/videos"
    poster_name = f"{video_name}_poster.jpg"
    if create_media:
        os.makedirs(build_dir, exist_ok=True)
        cmd = (
            f"ffmpeg -hide_banner -loglevel error -y -sseof -10 -i {src_dir}/{filename} "
            f"-frames:v 1 -vf \"scale='min(960,iw)':-2\" -q:v 7 {build_dir}/{poster_name}"
        )
        run_process(cmd)
    return f"videos/{dirname}/{poster_name}" if dirname else f"videos/{poster_name}"


def option_is_valid(option, chosen_keys):
    """
    Return whether `option` (one entry from an axis's "options" list) is
    compatible with `chosen_keys` (axis_name -> chosen key, for whichever
    earlier axes have a value so far). An option may restrict itself against
    an earlier axis by naming that axis as one of its own keys, mapping to
    the list of that axis's allowed keys; omitting an axis name means "valid
    for all values of that axis".
    """
    for axis_name, chosen_key in chosen_keys.items():
        # Only axes actually present in chosen_keys are checked here - a
        # restriction against an axis that was skipped (see
        # iter_axis_combinations) has no value to compare against, so it's
        # never evaluated and can't fail this option.
        if axis_name in option and chosen_key not in option[axis_name]:
            return False
    return True


def iter_axis_combinations(data, axis_names):
    """
    Yield every valid combination of axis options, as a dict of
    axis_name -> option, for the given ordered axis_names. Not every axis is
    guaranteed to be a key - some may be left out (see below). E.g. for
    axis_names = ["model", "property"], one yielded combination might be
    {"model": {"key": "thermal", "label": "Thermal AGN feedback"},
     "property": {"key": "densities", "label": "Gas density"}}.
    """
    def helper(remaining, chosen_options, chosen_keys):
        if not remaining:
            yield dict(chosen_options)
            return
        axis_name, rest = remaining[0], remaining[1:]
        # Axes are decided left to right: only options valid given the axes
        # already chosen (chosen_keys) are considered for this one.
        valid_options = [
            opt for opt in data[axis_name]["options"]
            if option_is_valid(opt, chosen_keys)
        ]
        if not valid_options:
            # Skip this axis entirely rather than pruning the branch - it's
            # left out of chosen_options/chosen_keys, not forced to any
            # value. E.g. under cluster's model=comparison, neither of
            # "alongside"'s options is valid, so "alongside" is skipped -
            # and since it never enters chosen_keys, any later axis's
            # restriction against "alongside" would never be evaluated for
            # this branch (see option_is_valid).
            yield from helper(rest, chosen_options, chosen_keys)
            return
        for opt in valid_options:
            yield from helper(
                rest,
                {**chosen_options, axis_name: opt},
                {**chosen_keys, axis_name: opt["key"]},
            )

    yield from helper(axis_names, {}, {})


def render_video_section(templates, section_id, section_key, title, description,
                          controls_html, initial_src, initial_poster, initial_nosound):
    """
    Render one interactive video section.(title, description, controls, video)
    """
    section_template = templates["video_section.html"]
    return template_replace(
        section_template,
        {
            "SECTION_ID": str(section_id),
            "SECTION_KEY": section_key,
            "SECTION_TITLE": title,
            "DESCRIPTION": description,
            "CONTROLS": controls_html,
            "INITIAL_SRC": initial_src,
            "INITIAL_POSTER": initial_poster,
            "INITIAL_NOSOUND": initial_nosound,
        },
    )


def make_video_section(templates, data, section_key, section_title, section_id, create_media):
    """
    Build one interactive video selector section (cluster/box/galaxy), fully
    driven by `data`. Returns (html, cfg), where cfg is the
    JSON-serializable per-section config embedded for the generic JS engine
    in videos.html (which re-runs the same combination logic client-side).

    The last axis in data["axes"] must be "property": it becomes the
    filename; every other axis becomes a nested directory level, using that
    axis's own option key as the directory name. A "_nosound" sibling file is
    checked for but is not itself an axis. It's not user-selectable,
    just an optional secondary download link.
    """
    axis_names = data["axes"]
    assert axis_names[-1] == "property", f"{section_key}: last axis must be 'property'"

    lookup = {}
    for combo in iter_axis_combinations(data, axis_names):
        assert "property" in combo, f"{section_key}: no valid property for {combo}"
        dirname = "/".join(
            [section_key] + [opt["key"] for name, opt in combo.items() if name != "property"]
        )
        base_name = combo["property"]["key"]
        src = copy_video_file(dirname, f"{base_name}.mp4", create_media)
        poster = make_video_poster(dirname, f"{base_name}.mp4", create_media)
        nosound = copy_video_file(dirname, f"{base_name}_nosound.mp4", create_media, required=False)
        key = "|".join(opt["key"] for name, opt in combo.items())
        lookup[key] = {"src": src, "poster": poster, "nosound": nosound}

    # Build the control skeletons - "property" is always a dropdown (it has
    # the most options, and is always the most specific axis); every other
    # axis is a row of pill buttons. The actual buttons/options are rendered
    # by the JS engine on page load, from the same "options" data below.
    # "control_order" (optional) lets a section display its controls in a
    # different order than "axes" requires for restriction/directory/lookup
    # purposes - it's purely a visual reordering of the same axis names.
    control_template = templates["video_axis_control.html"]
    controls = ""
    for axis_name in data.get("control_order", axis_names):
        control_type = "dropdown" if axis_name == "property" else "pills"
        inner = "<select></select>" if control_type == "dropdown" else '<div class="pill-group"></div>'
        controls += template_replace(
            control_template,
            {
                "SECTION_KEY": section_key,
                "AXIS": axis_name,
                "LABEL": data[axis_name]["label"],
                "CONTROL_TYPE": control_type,
                "CONTROL_INNER": inner,
            },
        )

    default_state = data["default"]
    initial = lookup["|".join(default_state[a] for a in axis_names)]

    description_axis = data.get("description_axis")
    if description_axis:
        description = next(
            opt["description"] for opt in data[description_axis]["options"]
            if opt["key"] == default_state[description_axis]
        )
    else:
        description = data.get("description", "")

    html = render_video_section(
        templates, section_id, section_key, section_title, description,
        controls, initial["src"], initial["poster"], initial["nosound"],
    )

    cfg = {
        "axes": axis_names,
        "options": {name: data[name]["options"] for name in axis_names},
        "state": dict(default_state),
        "lookup": lookup,
        "descriptionAxis": description_axis,
    }
    return html, cfg


def make_single_video_section(templates, section_id, title, video_info, create_media):
    """
    Build a plain, non-interactive single-video section (used for the
    standalone Sonification explanation video).
    """
    video_template = templates["video_single.html"]
    filename = video_info["name"]
    src = copy_video_file("", filename, create_media)
    poster = make_video_poster("", filename, create_media)
    return template_replace(
        video_template,
        {
            "VIDEO_DESCRIPTION": video_info.get("desc", ""),
            "VIDEO_THUMBNAIL": poster,
            "VIDEO_TITLE": title,
            "VIDEO_ID": str(section_id),
            "VIDEO_SRC": src,
        },
    )


def make_video_page(templates, videos_top, create_media):
    """
    Create the videos page: an interactive selector for each section whose
    entry in videos_top (src/videos.yml) has a "data" key (naming the yml
    file under src/ that defines it, and a "key" for its short section id),
    plus a standalone single-video section for any entry with a "name" key
    instead (e.g. the Sonification explanation).
    """
    page_template = templates["videos.html"]

    sections_html = ""
    all_cfg = {}
    for sid, (key, value) in enumerate(videos_top.items()):
        if key == "page_description":
            continue
        if "data" in value:
            with open(f"src/{value['data']}", "r") as handle:
                section_data = yaml.safe_load(handle)
            section_key = value["key"]
            html, cfg = make_video_section(templates, section_data, section_key, key, sid, create_media)
            all_cfg[section_key] = cfg
        else:
            html = make_single_video_section(templates, sid, key, value, create_media)
        sections_html += html

    with open("src/pages/videos.html", "w") as ofile:
        ofile.write(
            template_replace(
                page_template,
                {
                    "SECTIONS": sections_html,
                    "PAGE_DESCRIPTION": videos_top.get("page_description", ""),
                    "VIDEO_SECTIONS_JSON": json.dumps(all_cfg),
                },
            )
        )


def make_gallery(templates, input_sections, gallery_name, create_media):
    """
    Create the image gallery from the given gallery sections dictionary.

    If create_media=False then skip copying the images across.
    """

    # load all templates
    gallery_template = templates[f"gallery.html"]
    section_template = templates["gallery_section.html"]
    image_card_template = templates["image_card.html"]

    # loop over sections
    # modals are saved in one block, regardless of their section
    sections = ""
    for sid, (title, objects) in enumerate(input_sections.items()):
        if title in ['page_description', 'title']:
            continue
        # cards are grouped per section
        cards = ""
        # loop over this section's images
        for id, (obj_src, value) in enumerate(objects.items()):
            # generate a unique name for this image
            # this name will be used for thumbnail and image file names
            # it will also be used to identify the corresponding modal and
            # should therefore be unique
            obj_id = f"SEC{sid}IMG{id}"
            obj_type = 'image'
            obj_cap = value
            err_msg = f'Gallery object {gallery_name}/{obj_src} does not exist'
            assert os.path.exists(f'src/{gallery_name}/{obj_src}'), err_msg

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
        sections += template_replace(
            section_template, {"SECTION_TITLE": title, "SECTION_ID": "sec" + str(sid),
                                "IMG_CARDS": cards}
        )

    # save the html
    with open(f"src/pages/{gallery_name}.html", "w") as ofile:
        ofile.write(template_replace(gallery_template, {"PAGE_DESCRIPTION": input_sections.get('page_description', ''), "IMG_SECTIONS": sections, "GALLERY_NAME": input_sections['title']}))


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
        help='Generate papers and team map',
    )
    args = parser.parse_args()
    if args.update:
        clean_build(keep_sliders=False, keep_images=False, keep_videos=False)
        # Update papers
        generate_publication_list.generate_publication_list(skip_query=False)
        with open("src/pages.yml", "r") as handle:
            pages = yaml.safe_load(handle)
        for page in ['papers.html']:
            make_page(page, pages, templates)
        # Update map
        generate_user_map.generate_user_map()
        copy_assets()
        copy_paper_data()
        exit()

    # Whether to skip build steps to allow for a quick website build
    keep_sliders = True
    keep_images = True
    keep_videos = True
    skip_ads_query = False

    # Clean up any existing build, create new build directories
    keep_sliders, keep_images, keep_videos = clean_build(
        keep_sliders=keep_sliders,
        keep_images=keep_images,
        keep_videos=keep_videos,
    )

    # Generate the image gallery
    with open("src/images.yml", "r") as handle:
        images = yaml.safe_load(handle)
    make_gallery(templates, images, 'images', not keep_images)

    # Generate the video page
    with open("src/videos.yml", "r") as handle:
        videos_config = yaml.safe_load(handle)
    make_video_page(templates, videos_config, not keep_videos)

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
    copy_paper_data()
    copy_styles()
    if not keep_sliders:
        copy_slider_images()
