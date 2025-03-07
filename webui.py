import gradio as gr
import random
import time
import shared
import argparse
import modules.path
import fooocus_version
import modules.html
import modules.async_worker as worker
import modules.constants as constants
import json

from modules.settings import default_settings
from modules.resolutions import get_resolution_string, resolutions
from modules.sdxl_styles import style_keys
from collections.abc import Mapping
from PIL import Image


GALLERY_ID_INPUT = 0
GALLERY_ID_REVISION = 1
GALLERY_ID_OUTPUT = 2


def generate_clicked(*args):
    yield gr.update(interactive=False), \
        gr.update(visible=True, value=modules.html.make_progress_html(1, 'Processing text encoding ...')), \
        gr.update(visible=True, value=None), \
        gr.update(visible=False), \
        gr.update(), \
        gr.update(value=None), \
        gr.update()

    worker.buffer.append(list(args))
    finished = False

    while not finished:
        time.sleep(0.01)
        if len(worker.outputs) > 0:
            flag, product = worker.outputs.pop(0)
            if flag == 'preview':
                percentage, title, image = product
                yield gr.update(interactive=False), \
                    gr.update(visible=True, value=modules.html.make_progress_html(percentage, title)), \
                    gr.update(visible=True, value=image) if image is not None else gr.update(), \
                    gr.update(visible=False), \
                    gr.update(), \
                    gr.update(), \
                    gr.update()
            if flag == 'results':
                yield gr.update(interactive=True), \
                    gr.update(visible=False), \
                    gr.update(visible=False), \
                    gr.update(visible=True), \
                    gr.update(value=product), \
                    gr.update(), \
                    gr.update()
            if flag == 'metadatas':
                yield gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(value=product), gr.update(selected=GALLERY_ID_OUTPUT)
                finished = True
    return


def metadata_to_ctrls(metadata, ctrls):
    if not isinstance(metadata, Mapping):
        return ctrls

    if 'prompt' in metadata:
        ctrls[0] = metadata['prompt']
    if 'negative_prompt' in metadata:
        ctrls[1] = metadata['negative_prompt']
    if 'style' in metadata:
        ctrls[2] = metadata['style']
    if 'performance' in metadata:
        ctrls[3] = metadata['performance']
    if 'width' in metadata and 'height' in metadata:
        ctrls[4] = get_resolution_string(metadata['width'], metadata['height'])
    elif 'resolution' in metadata:
        ctrls[4] = metadata['resolution']
    # image_number
    if 'seed' in metadata:
        ctrls[6] = metadata['seed']
        ctrls[47] = False
    if 'sharpness' in metadata:
        ctrls[7] = metadata['sharpness']
    if 'sampler_name' in metadata:
        ctrls[8] = metadata['sampler_name']
    elif 'sampler' in metadata:
        ctrls[8] = metadata['sampler']
    if 'scheduler' in metadata:
        ctrls[9] = metadata['scheduler']
    if 'steps' in metadata:
        ctrls[10] = metadata['steps']
        if ctrls[10] == constants.STEPS_SPEED:
            ctrls[3] = 'Speed'
        elif ctrls[10] == constants.STEPS_QUALITY:
            ctrls[3] = 'Quality'
        else:
            ctrls[3] = 'Custom'
    if 'switch' in metadata:
        ctrls[11] = round(metadata['switch'] / ctrls[10], 2)
        if ctrls[11] != round(constants.SWITCH_SPEED / constants.STEPS_SPEED, 2):
            ctrls[3] = 'Custom'
    if 'cfg' in metadata:
        ctrls[12] = metadata['cfg']
    if 'base_model' in metadata:
        ctrls[13] = metadata['base_model']
    elif 'base_model_name' in metadata:
        ctrls[13] = metadata['base_model_name']
    if 'refiner_model' in metadata:
        ctrls[14] = metadata['refiner_model']
    elif 'refiner_model_name' in metadata:
        ctrls[14] = metadata['refiner_model_name']
    if 'base_clip_skip' in metadata:
        ctrls[15] = metadata['base_clip_skip']
    if 'refiner_clip_skip' in metadata:
        ctrls[16] = metadata['refiner_clip_skip']
    if 'l1' in metadata:
        ctrls[17] = metadata['l1']
    if 'w1' in metadata:
        ctrls[18] = metadata['w1']
    if 'l2' in metadata:
        ctrls[19] = metadata['l2']
    if 'w2' in metadata:
        ctrls[20] = metadata['w2']
    if 'l3' in metadata:
        ctrls[21] = metadata['l3']
    if 'w3' in metadata:
        ctrls[22] = metadata['w3']
    if 'l4' in metadata:
        ctrls[23] = metadata['l4']
    if 'w4' in metadata:
        ctrls[24] = metadata['w4']
    if 'l5' in metadata:
        ctrls[25] = metadata['l5']
    if 'w5' in metadata:
        ctrls[26] = metadata['w5']
    # save_metadata_json
    # save_metadata_image
    if 'img2img' in metadata:
        ctrls[29] = metadata['img2img']
        if 'start_step' in metadata:
            if ctrls[3] == 'Speed':
                ctrls[30] = round(metadata['start_step'] / constants.STEPS_SPEED, 2)
            elif ctrls[3] == 'Quality':
                ctrls[30] = round(metadata['start_step'] / constants.STEPS_QUALITY, 2)
            else:
                ctrls[30] = round(metadata['start_step'] / ctrls[10], 2)
        if 'denoise' in metadata:
            ctrls[31] = metadata['denoise']
    if 'revision' in metadata:
        ctrls[32] = metadata['revision']
    if 'zero_out' in metadata:
        ctrls[33] = metadata['zero_out_positive']
    if 'zero_out' in metadata:
        ctrls[34] = metadata['zero_out_negative']
    if 'revision_strength_1' in metadata:
        ctrls[35] = metadata['revision_strength_1']
    if 'revision_strength_2' in metadata:
        ctrls[36] = metadata['revision_strength_2']
    if 'revision_strength_3' in metadata:
        ctrls[37] = metadata['revision_strength_3']
    if 'revision_strength_4' in metadata:
        ctrls[38] = metadata['revision_strength_4']
    # same_seed_for_all
    # output_format
    if 'control_lora_canny' in metadata:
        ctrls[41] = metadata['control_lora_canny']
    if 'canny_edge_low' in metadata:
        ctrls[42] = metadata['canny_edge_low']
    if 'canny_edge_high' in metadata:
        ctrls[43] = metadata['canny_edge_high']
    if 'canny_start' in metadata:
        ctrls[44] = metadata['canny_start']
    if 'canny_stop' in metadata:
        ctrls[45] = metadata['canny_stop']
    if 'canny_strength' in metadata:
        ctrls[46] = metadata['canny_strength']
    # seed_random
    return ctrls    


def load_prompt_handler(_file, *args):
    ctrls=list(args)
    path = _file.name
    if path.endswith('.json'):
        with open(path, encoding='utf-8') as json_file:
            try:
                json_obj = json.load(json_file)
                metadata_to_ctrls(json_obj, ctrls)
            except Exception as e:
                print(e)
            finally:
                json_file.close()
    else:
        with open(path, 'rb') as image_file:
            image = Image.open(image_file)
            image_file.close()

            if path.endswith('.png') and 'Comment' in image.info:
                metadata_string = image.info['Comment']
            elif path.endswith('.jpg') and 'comment' in image.info:
                metadata_string = image.info['comment']
            else:
                metadata_string = None

            if metadata_string != None:
                try:
                    metadata = json.loads(metadata_string)
                    metadata_to_ctrls(metadata, ctrls)
                except Exception as e:
                    print(e)
    return ctrls


def load_input_images_handler(files):
    return list(map(lambda x: x.name, files)), gr.update(selected=GALLERY_ID_INPUT), gr.update(value=len(files))


def load_revision_images_handler(files):
    return gr.update(value=True), list(map(lambda x: x.name, files[:4])), gr.update(selected=GALLERY_ID_REVISION)


def output_to_input_handler(gallery):
    if len(gallery) == 0:
        return [], gr.update()
    else:
        return list(map(lambda x: x['name'], gallery)), gr.update(selected=GALLERY_ID_INPUT)


def output_to_revision_handler(gallery):
    if len(gallery) == 0:
        return gr.update(value=False), [], gr.update()
    else:
        return gr.update(value=True), list(map(lambda x: x['name'], gallery[:4])), gr.update(selected=GALLERY_ID_REVISION)


settings = default_settings

shared.gradio_root = gr.Blocks(title=fooocus_version.full_version, css=modules.html.css).queue()
with shared.gradio_root:
    with gr.Row():
        with gr.Column(scale=2):
            progress_window = gr.Image(label='Preview', show_label=True, height=640, visible=False)
            progress_html = gr.HTML(value=modules.html.make_progress_html(32, 'Progress 32%'), visible=False, elem_id='progress-bar', elem_classes='progress-bar')
            with gr.Column() as gallery_holder:
                with gr.Tabs(selected=GALLERY_ID_OUTPUT) as gallery_tabs:
                    with gr.Tab(label='Input', id=GALLERY_ID_INPUT):
                        input_gallery = gr.Gallery(label='Input', show_label=False, object_fit='contain', height=720, visible=True)
                    with gr.Tab(label='Revision', id=GALLERY_ID_REVISION):
                        revision_gallery = gr.Gallery(label='Revision', show_label=False, object_fit='contain', height=720, visible=True)
                    with gr.Tab(label='Output', id=GALLERY_ID_OUTPUT):
                        output_gallery = gr.Gallery(label='Output', show_label=False, object_fit='contain', height=720, visible=True)
            with gr.Row(elem_classes='type_row'):
                with gr.Column(scale=17):
                    prompt = gr.Textbox(show_label=False, placeholder='Type prompt here.', container=False, autofocus=True, elem_classes='type_row', lines=1024, value=settings['prompt'])
                with gr.Column(scale=3, min_width=0):
                    with gr.Row():
                        img2img_mode = gr.Checkbox(label='Image-2-Image', value=settings['img2img_mode'], elem_classes='type_small_row')
                    with gr.Row():
                        run_button = gr.Button(label='Generate', value='Generate', elem_classes='type_small_row')
            with gr.Row():
                advanced_checkbox = gr.Checkbox(label='Advanced', value=settings['advanced_mode'], container=False)

        with gr.Column(scale=1, visible=settings['advanced_mode']) as advanced_column:
            with gr.Tab(label='Settings'):
                performance = gr.Radio(label='Performance', choices=['Speed', 'Quality', 'Custom'], value=settings['performance'])
                with gr.Row():
                    custom_steps = gr.Slider(label='Custom Steps', minimum=10, maximum=200, step=1, value=settings['custom_steps'], visible=settings['performance'] == 'Custom')
                    custom_switch = gr.Slider(label='Custom Switch', minimum=0.2, maximum=1.0, step=0.01, value=settings['custom_switch'], visible=settings['performance'] == 'Custom')
                resolution = gr.Dropdown(label='Resolution (width × height)', choices=list(resolutions.keys()), value=settings['resolution'])
                style_selection = gr.Dropdown(label='Style', choices=style_keys, value=settings['style'])
                image_number = gr.Slider(label='Image Number', minimum=1, maximum=32, step=1, value=settings['image_number'])
                negative_prompt = gr.Textbox(label='Negative Prompt', show_label=True, placeholder="Type prompt here.", value=settings['negative_prompt'])
                with gr.Row():
                   seed_random = gr.Checkbox(label='Random', value=settings['seed_random'])
                   same_seed_for_all = gr.Checkbox(label='Same seed for all images', value=settings['same_seed_for_all'])
                image_seed = gr.Textbox(label='Seed', value=settings['seed'], max_lines=1, visible=not settings['seed_random'])
                with gr.Row():
                    load_prompt_button = gr.UploadButton(label='Load Prompt', file_count='single', file_types=['.json', '.png', '.jpg'], elem_classes='type_small_row', min_width=0)

                def random_checked(r):
                    return gr.update(visible=not r)

                def refresh_seed(r, seed_string):
                    try:
                        seed_value = int(seed_string) 
                    except Exception as e:
                        seed_value = -1
                    if r or not isinstance(seed_value, int) or seed_value < constants.MIN_SEED or seed_value > constants.MAX_SEED:
                        return random.randint(constants.MIN_SEED, constants.MAX_SEED)
                    else:
                        return seed_value

                seed_random.change(random_checked, inputs=[seed_random], outputs=[image_seed])

                def performance_changed(value):
                    return gr.update(visible=value == 'Custom'), gr.update(visible=value == 'Custom')

                performance.change(fn=performance_changed, inputs=[performance], outputs=[custom_steps, custom_switch])

            with gr.Tab(label='Image-2-Image'):
                revision_mode = gr.Checkbox(label='Revision (prompting with images)', value=settings['revision_mode'])
                revision_strength_1 = gr.Slider(label='Revision Strength for Image 1', minimum=-2, maximum=2, step=0.01, value=settings['revision_strength_1'])
                revision_strength_2 = gr.Slider(label='Revision Strength for Image 2', minimum=-2, maximum=2, step=0.01, value=settings['revision_strength_2'])
                revision_strength_3 = gr.Slider(label='Revision Strength for Image 3', minimum=-2, maximum=2, step=0.01, value=settings['revision_strength_3'])
                revision_strength_4 = gr.Slider(label='Revision Strength for Image 4', minimum=-2, maximum=2, step=0.01, value=settings['revision_strength_4'])
                with gr.Row():
                    zero_out_positive = gr.Checkbox(label='Zero Out Positive Prompt', value=settings['zero_out_positive'])
                    zero_out_negative = gr.Checkbox(label='Zero Out Negative Prompt', value=settings['zero_out_negative'])

                img2img_start_step = gr.Slider(label='Image-2-Image Start Step', minimum=0.0, maximum=0.8, step=0.01, value=settings['img2img_start_step'])
                img2img_denoise = gr.Slider(label='Image-2-Image Denoise', minimum=0.2, maximum=1.0, step=0.01, value=settings['img2img_denoise'])

                keep_input_names = gr.Checkbox(label='Keep Input Names', value=settings['keep_input_names'], elem_classes='type_small_row')
                with gr.Row():
                    load_input_images_button = gr.UploadButton(label='Load Image(s) to Input', file_count='multiple', file_types=["image"], elem_classes='type_small_row', min_width=0)
                    load_revision_images_button = gr.UploadButton(label='Load Image(s) to Revision', file_count='multiple', file_types=["image"], elem_classes='type_small_row', min_width=0)
                with gr.Row():
                    output_to_input_button = gr.Button(label='Output to Input', value='Output to Input', elem_classes='type_small_row', min_width=0)
                    output_to_revision_button = gr.Button(label='Output to Revision', value='Output to Revision', elem_classes='type_small_row', min_width=0)

                load_input_images_button.upload(fn=load_input_images_handler, inputs=[load_input_images_button], outputs=[input_gallery, gallery_tabs, image_number])
                load_revision_images_button.upload(fn=load_revision_images_handler, inputs=[load_revision_images_button], outputs=[revision_mode, revision_gallery, gallery_tabs])
                output_to_input_button.click(output_to_input_handler, inputs=output_gallery, outputs=[input_gallery, gallery_tabs])
                output_to_revision_button.click(output_to_revision_handler, inputs=output_gallery, outputs=[revision_mode, revision_gallery, gallery_tabs])

                img2img_ctrls = [img2img_mode, img2img_start_step, img2img_denoise, revision_mode, zero_out_positive, zero_out_negative,
                    revision_strength_1, revision_strength_2, revision_strength_3, revision_strength_4]

                def verify_revision(rev, gallery_in, gallery_rev, gallery_out):
                    if rev and len(gallery_rev) == 0:
                        if len(gallery_in) > 0:
                            gr.Info('Revision: imported input')
                            return gr.update(), list(map(lambda x: x['name'], gallery_in[:1]))
                        elif len(gallery_out) > 0:
                            gr.Info('Revision: imported output')
                            return gr.update(), list(map(lambda x: x['name'], gallery_out[:1]))
                        else:
                            gr.Warning('Revision: disabled (no images available)')
                            return gr.update(value=False), gr.update()
                    else:
                        return gr.update(), gr.update()

            with gr.Tab(label='CN'):
                control_lora_canny = gr.Checkbox(label='Control-LoRA: Canny', value=settings['control_lora_canny'])
                canny_edge_low = gr.Slider(label='Edge Detection Low', minimum=0.0, maximum=1.0, step=0.01, value=settings['canny_edge_low'])
                canny_edge_high = gr.Slider(label='Edge Detection High', minimum=0.0, maximum=1.0, step=0.01, value=settings['canny_edge_high'])
                canny_start = gr.Slider(label='Canny Start', minimum=0.0, maximum=1.0, step=0.01, value=settings['canny_start'])
                canny_stop = gr.Slider(label='Canny Stop', minimum=0.0, maximum=1.0, step=0.01, value=settings['canny_stop'])
                canny_strength = gr.Slider(label='Canny Strength', minimum=0.0, maximum=1.0, step=0.01, value=settings['canny_strength'])

                canny_ctrls = [control_lora_canny, canny_edge_low, canny_edge_high, canny_start, canny_stop, canny_strength]

            with gr.Tab(label='Models'):
                with gr.Row():
                    base_model = gr.Dropdown(label='SDXL Base Model', choices=modules.path.model_filenames, value=settings['base_model'], show_label=True)
                    refiner_model = gr.Dropdown(label='SDXL Refiner', choices=['None'] + modules.path.model_filenames, value=settings['refiner_model'], show_label=True)
                with gr.Accordion(label='LoRAs', open=True):
                    lora_ctrls = []
                    for i in range(5):
                        with gr.Row():
                            lora_model = gr.Dropdown(label=f'SDXL LoRA {i+1}', choices=['None'] + modules.path.lora_filenames, value=settings[f'lora_{i+1}_model'])
                            lora_weight = gr.Slider(label='Weight', minimum=-2, maximum=2, step=0.01, value=settings[f'lora_{i+1}_weight'])
                            lora_ctrls += [lora_model, lora_weight]
                with gr.Row():
                    model_refresh = gr.Button(label='Refresh', value='\U0001f504 Refresh All Files', variant='secondary', elem_classes='refresh_button')

            with gr.Tab(label='Sampling'):
                cfg = gr.Slider(label='CFG', minimum=1.0, maximum=20.0, step=0.1, value=settings['cfg'])
                base_clip_skip = gr.Slider(label='Base CLIP Skip', minimum=-10, maximum=-1, step=1, value=settings['base_clip_skip'])
                refiner_clip_skip = gr.Slider(label='Refiner CLIP Skip', minimum=-10, maximum=-1, step=1, value=settings['refiner_clip_skip'])
                sampler_name = gr.Dropdown(label='Sampler', choices=['dpmpp_2m_sde_gpu', 'dpmpp_2m_sde', 'dpmpp_3m_sde_gpu', 'dpmpp_3m_sde',
                    'dpmpp_sde_gpu', 'dpmpp_sde', 'dpmpp_2m', 'dpmpp_2s_ancestral', 'euler', 'euler_ancestral', 'heun', 'dpm_2', 'dpm_2_ancestral'], value=settings['sampler'])
                scheduler = gr.Dropdown(label='Scheduler', choices=['karras', 'exponential', 'simple', 'ddim_uniform'], value=settings['scheduler'])
                sharpness = gr.Slider(label='Sampling Sharpness', minimum=0.0, maximum=40.0, step=0.01, value=settings['sharpness'])
                gr.HTML('<a href="https://github.com/lllyasviel/Fooocus/discussions/117">\U0001F4D4 Document</a>')

                def model_refresh_clicked():
                    modules.path.update_all_model_names()
                    results = []
                    results += [gr.update(choices=modules.path.model_filenames), gr.update(choices=['None'] + modules.path.model_filenames)]
                    for i in range(5):
                        results += [gr.update(choices=['None'] + modules.path.lora_filenames), gr.update()]
                    return results

                model_refresh.click(model_refresh_clicked, [], [base_model, refiner_model] + lora_ctrls)

            with gr.Tab(label='Misc'):
                output_format = gr.Radio(label='Output Format', choices=['png', 'jpg'], value=settings['output_format'])
                with gr.Row():
                    save_metadata_json = gr.Checkbox(label='Save Metadata in JSON', value=settings['save_metadata_json'])
                    save_metadata_image = gr.Checkbox(label='Save Metadata in Image', value=settings['save_metadata_image'])
                metadata_viewer = gr.JSON(label='Metadata')

        advanced_checkbox.change(lambda x: gr.update(visible=x), advanced_checkbox, advanced_column)

        def verify_input(img2img, canny, gallery_in, gallery_rev, gallery_out):
            if (img2img or canny) and len(gallery_in) == 0:
                if len(gallery_rev) > 0:
                    gr.Info('Image-2-Image / CL: imported revision as input')
                    return gr.update(), gr.update(), list(map(lambda x: x['name'], gallery_rev[:1]))
                elif len(gallery_out) > 0:
                    gr.Info('Image-2-Image / CL: imported output as input')
                    return gr.update(), gr.update(), list(map(lambda x: x['name'], gallery_out[:1]))
                else:
                    gr.Warning('Image-2-Image / CL: disabled (no images available)')
                    return gr.update(value=False), gr.update(value=False), gr.update()
            else:
                return gr.update(), gr.update(), gr.update()


        ctrls = [
            prompt, negative_prompt, style_selection,
            performance, resolution, image_number, image_seed, sharpness, sampler_name, scheduler,
            custom_steps, custom_switch, cfg
        ]
        ctrls += [base_model, refiner_model, base_clip_skip, refiner_clip_skip] + lora_ctrls + [save_metadata_json, save_metadata_image] \
            + img2img_ctrls + [same_seed_for_all, output_format] + canny_ctrls
        load_prompt_button.upload(fn=load_prompt_handler, inputs=[load_prompt_button] + ctrls + [seed_random], outputs=ctrls + [seed_random])
        run_button.click(fn=refresh_seed, inputs=[seed_random, image_seed], outputs=image_seed) \
            .then(fn=verify_input, inputs=[img2img_mode, control_lora_canny, input_gallery, revision_gallery, output_gallery], outputs=[img2img_mode, control_lora_canny, input_gallery]) \
            .then(fn=verify_revision, inputs=[revision_mode, input_gallery, revision_gallery, output_gallery], outputs=[revision_mode, revision_gallery]) \
            .then(fn=generate_clicked, inputs=ctrls + [input_gallery, revision_gallery, keep_input_names],
                outputs=[run_button, progress_html, progress_window, gallery_holder, output_gallery, metadata_viewer, gallery_tabs])

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=None, help="Set the listen port.")
parser.add_argument("--share", action='store_true', help="Set whether to share on Gradio.")
parser.add_argument("--listen", type=str, default=None, metavar="IP", nargs="?", const="0.0.0.0", help="Set the listen interface.")
args = parser.parse_args()
shared.gradio_root.launch(inbrowser=True, server_name=args.listen, server_port=args.port, share=args.share)
