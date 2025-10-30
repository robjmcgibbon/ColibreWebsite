########## Script for generating mass function data
# import swiftsimio as sw
# import numpy as np
#
# # Setting vmin as 100x initial gas mass
# for run, run_name, vmin in [
#         ('L0025N0752/Thermal', 'L025m5', 2.3e7),
#         ('L0200N3008/Thermal', 'L200m6', 1.8e8),
#         ('L0400N3008/Thermal', 'L400m7', 1.5e9),
#     ]:
#     for snap, z in [
#             (127, '0'),
#             (92, '1'),
#             (64, '3'),
#             (26, '8'),
#         ]:
#         base_dir= '/cosma8/data/dp004/colibre/Runs'
#         filename = f'{base_dir}/{run}/SOAP-HBT/halo_properties_{snap:04}.hdf5'
#         soap = sw.load(filename)
#
#         for prop, npart, prop_name in [
#                 (
#                     soap.exclusive_sphere_50kpc.stellar_mass,
#                     soap.exclusive_sphere_50kpc.number_of_star_particles,
#                     'Stellar_mass',
#                 ),
#                 (
#                     soap.spherical_overdensity_200_crit.total_mass,
#                     soap.input_halos.number_of_bound_particles,
#                     'Halo_mass',
#                 ),
#             ]:
#             vmax = 1.001 * np.max(prop.to_physical_value('Msun'))
#             bins = 10 ** np.arange(np.log10(vmin), np.log10(vmax), 0.1)
#             mids = (bins[1:] + bins[:-1]) / 2
#             n, _ = np.histogram(prop.to_physical_value('Msun'), bins=bins)
#
#             # Convert to cumulative
#             n = np.cumsum(n[::-1])[::-1]
#
#             print(f'{prop_name}_z{z}_{run_name}')
#             np.savetxt(
#                 f'{prop_name}_z{z}_{run_name}.txt',
#                 np.vstack([n, mids]).T,
#                 header='n_sub,mass',
#                 comments='',
#                 delimiter=',',
#             )
##########

import pandas as pd
import glob, os
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Select, CustomJS, Div, HoverTool
from bokeh.plotting import figure
from bokeh.layouts import column, row

def generate_mass_functions():
    ### Load the data
    data = {}
    for run_name in ['L025m5', 'L200m6', 'L400m7']:
        for z in ['0', '1', '3', '8']:
            for prop_name in ['Stellar_mass', 'Halo_mass']: 
                filename = f'{prop_name}_z{z}_{run_name}.txt'

                df = pd.read_csv(f'src/assets/simulations/{filename}')
                data[(prop_name.replace('_', ' '), z, run_name)] = df

    # Convert to JSON-friendly structure for JS
    js_data = {f"{p}_{z}_{s}": df.to_dict(orient="list") for (p, z, s), df in data.items()}

    ### Dropdown options
    property_options = sorted({k[0] for k in data.keys()})
    redshift_options = sorted({k[1] for k in data.keys()})
    simulation_options = sorted({k[2] for k in data.keys()})
    prop_default = 'Stellar mass'
    z_default = '0'
    sim_default = 'L200m6'

    init_key = f"{prop_default}_{z_default}_{sim_default}"
    source = ColumnDataSource(js_data[init_key])

    ### Styling parameters
    font_size = "20px"

    ### Plot
    p = figure(
        x_axis_type="log", y_axis_type="log",
        sizing_mode="scale_width",
        aspect_ratio=1.9,
        tools="",
    )
    p.toolbar_location = None
    p.line("mass", "n_sub", source=source, line_width=2)
    p.xaxis.axis_label = "Stellar mass [Msun]"
    p.xaxis.axis_label_text_font_size = font_size
    p.xaxis.major_label_text_font_size = font_size
    p.xaxis.axis_label_text_font_style = 'bold'
    p.yaxis.axis_label = "Number of galaxies (cumulative)"
    p.yaxis.axis_label_text_font_size = font_size
    p.yaxis.major_label_text_font_size = font_size
    p.yaxis.axis_label_text_font_style = 'bold'

    ### Widgets (set title="" so the Div label is the only label rendered)
    prop_select = Select(title="", value=prop_default, options=property_options)
    z_select = Select(title="", value=str(z_default), options=[str(z) for z in redshift_options])
    sim_select = Select(title="", value=sim_default, options=simulation_options)

    ### Create styled labels
    font_size = "20px"
    prop_label = Div(text=f"<b style='font-size:{font_size}'>Property:</b>", width=90, height=30, styles={"margin": '13px'})
    z_label    = Div(text=f"<b style='font-size:{font_size}'>Redshift:</b>", width=90, height=30, styles={"margin": '13px'})
    sim_label  = Div(text=f"<b style='font-size:{font_size}'>Simulation:</b>", width=110, height=30, styles={"margin": '13px'})
    for s in [prop_select, z_select, sim_select]:
        s.css_classes = ["custom-select"]
        s.styles = {
            "font-size": font_size,
            "margin": '0px',
            "padding_right": "10px",
            "padding_top": "10px",
        }

    ### Row layout
    controls = row(
        prop_label, prop_select,
        z_label, z_select,
        sim_label, sim_select,
        margin=(10, 0, 10, 100),  # top, right, bottom, left
    )

    ### CustomJS callback: updates data and axis label
    callback = CustomJS(
        args=dict(
            source=source,
            all_data=js_data,
            prop=prop_select,
            z=z_select,
            sim=sim_select,
            xaxis=p.xaxis[0],
            yaxis=p.yaxis[0],
        ),
        code="""
        const key = `${prop.value}_${z.value}_${sim.value}`;
        const new_data = all_data[key];
        // Replace source data (Bokeh expects arrays)
        source.data = {
            mass: new_data['mass'],
            n_sub: new_data['n_sub']
        };

        // Update axis labels based on property
        if (prop.value === "Stellar mass") {
            xaxis.axis_label = "Stellar mass [Msun]";
            yaxis.axis_label = "Number of galaxies (cumulative)";
        } else if (prop.value === "Halo mass") {
            xaxis.axis_label = "M200c [Msun]";
            yaxis.axis_label = "Number of halos (cumulative)";
        } else {
            // fallback
            xaxis.axis_label = "Undefined";
            yaxis.axis_label = "Undefined";
        }

        // Propagate changes
        xaxis.change.emit();
        yaxis.change.emit();
        source.change.emit();
    """
    )
    prop_select.js_on_change("value", callback)
    z_select.js_on_change("value", callback)
    sim_select.js_on_change("value", callback)

    ### Add data when hovering
    hover = HoverTool(
        tooltips=[
            ("N", "@n_sub{0}"),
        ],
        mode="vline"  # shows tooltip for nearest x value along vertical line
    )
    p.add_tools(hover)

    ### Save
    layout = column(controls, p, sizing_mode="stretch_both")
    save(
        layout,
        'src/assets/simulations/mass_functions.html',
        title="Interactive Mass Function",
        resources='inline',
    )

if __name__ == '__main__':
    generate_mass_functions()

