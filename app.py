
from curses.ascii import SUB
import os

import json
import re
import flask

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from werkzeug.utils import secure_filename

app = Flask(__name__)


from transcription import SUBTITLE_LOCAL_DIRECTORY, VIDEO_LOCAL_DIRECTORY, generate_video_subtitles, dummy

os.makedirs(VIDEO_LOCAL_DIRECTORY, exist_ok=True)


VIDEO_FILENAME_FORMATS = (
    '.264', '.3g2', '.3gp', '.3gp2', '.3gpp', '.3gpp2', '.3mm', '.3p2', '.60d', '.787', '.89', '.aaf', '.aec', '.aep', '.aepx',
    '.aet', '.aetx', '.ajp', '.ale', '.am', '.amc', '.amv', '.amx', '.anim', '.aqt', '.arcut', '.arf', '.asf', '.asx', '.avb',
    '.avc', '.avd', '.avi', '.avp', '.avs', '.avs', '.avv', '.axm', '.bdm', '.bdmv', '.bdt2', '.bdt3', '.bik', '.bin', '.bix',
    '.bmk', '.bnp', '.box', '.bs4', '.bsf', '.bvr', '.byu', '.camproj', '.camrec', '.camv', '.ced', '.cel', '.cine', '.cip',
    '.clpi', '.cmmp', '.cmmtpl', '.cmproj', '.cmrec', '.cpi', '.cst', '.cvc', '.cx3', '.d2v', '.d3v', '.dat', '.dav', '.dce',
    '.dck', '.dcr', '.dcr', '.ddat', '.dif', '.dir', '.divx', '.dlx', '.dmb', '.dmsd', '.dmsd3d', '.dmsm', '.dmsm3d', '.dmss',
    '.dmx', '.dnc', '.dpa', '.dpg', '.dream', '.dsy', '.dv', '.dv-avi', '.dv4', '.dvdmedia', '.dvr', '.dvr-ms', '.dvx', '.dxr',
    '.dzm', '.dzp', '.dzt', '.edl', '.evo', '.eye', '.ezt', '.f4p', '.f4v', '.fbr', '.fbr', '.fbz', '.fcp', '.fcproject',
    '.ffd', '.flc', '.flh', '.fli', '.flv', '.flx', '.gfp', '.gl', '.gom', '.grasp', '.gts', '.gvi', '.gvp', '.h264', '.hdmov',
    '.hkm', '.ifo', '.imovieproj', '.imovieproject', '.ircp', '.irf', '.ism', '.ismc', '.ismv', '.iva', '.ivf', '.ivr', '.ivs',
    '.izz', '.izzy', '.jss', '.jts', '.jtv', '.k3g', '.kmv', '.ktn', '.lrec', '.lsf', '.lsx', '.m15', '.m1pg', '.m1v', '.m21',
    '.m21', '.m2a', '.m2p', '.m2t', '.m2ts', '.m2v', '.m4e', '.m4u', '.m4v', '.m75', '.mani', '.meta', '.mgv', '.mj2', '.mjp',
    '.mjpg', '.mk3d', '.mkv', '.mmv', '.mnv', '.mob', '.mod', '.modd', '.moff', '.moi', '.moov', '.mov', '.movie', '.mp21',
    '.mp21', '.mp2v', '.mp4', '.mp4v', '.mpe', '.mpeg', '.mpeg1', '.mpeg4', '.mpf', '.mpg', '.mpg2', '.mpgindex', '.mpl',
    '.mpl', '.mpls', '.mpsub', '.mpv', '.mpv2', '.mqv', '.msdvd', '.mse', '.msh', '.mswmm', '.mts', '.mtv', '.mvb', '.mvc',
    '.mvd', '.mve', '.mvex', '.mvp', '.mvp', '.mvy', '.mxf', '.mxv', '.mys', '.ncor', '.nsv', '.nut', '.nuv', '.nvc', '.ogm',
    '.ogv', '.ogx', '.osp', '.otrkey', '.pac', '.par', '.pds', '.pgi', '.photoshow', '.piv', '.pjs', '.playlist', '.plproj',
    '.pmf', '.pmv', '.pns', '.ppj', '.prel', '.pro', '.prproj', '.prtl', '.psb', '.psh', '.pssd', '.pva', '.pvr', '.pxv',
    '.qt', '.qtch', '.qtindex', '.qtl', '.qtm', '.qtz', '.r3d', '.rcd', '.rcproject', '.rdb', '.rec', '.rm', '.rmd', '.rmd',
    '.rmp', '.rms', '.rmv', '.rmvb', '.roq', '.rp', '.rsx', '.rts', '.rts', '.rum', '.rv', '.rvid', '.rvl', '.sbk', '.sbt',
    '.scc', '.scm', '.scm', '.scn', '.screenflow', '.sec', '.sedprj', '.seq', '.sfd', '.sfvidcap', '.siv', '.smi', '.smi',
    '.smil', '.smk', '.sml', '.smv', '.spl', '.sqz', '.srt', '.ssf', '.ssm', '.stl', '.str', '.stx', '.svi', '.swf', '.swi',
    '.swt', '.tda3mt', '.tdx', '.thp', '.tivo', '.tix', '.tod', '.tp', '.tp0', '.tpd', '.tpr', '.trp', '.ts', '.tsp', '.ttxt',
    '.tvs', '.usf', '.usm', '.vc1', '.vcpf', '.vcr', '.vcv', '.vdo', '.vdr', '.vdx', '.veg','.vem', '.vep', '.vf', '.vft',
    '.vfw', '.vfz', '.vgz', '.vid', '.video', '.viewlet', '.viv', '.vivo', '.vlab', '.vob', '.vp3', '.vp6', '.vp7', '.vpj',
    '.vro', '.vs4', '.vse', '.vsp', '.w32', '.wcp', '.webm', '.wlmp', '.wm', '.wmd', '.wmmp', '.wmv', '.wmx', '.wot', '.wp3',
    '.wpl', '.wtv', '.wve', '.wvx', '.xej', '.xel', '.xesc', '.xfl', '.xlmv', '.xmv', '.xvid', '.y4m', '.yog', '.yuv', '.zeg',
    '.zm1', '.zm2', '.zm3', '.zmv'
)

@app.route('/', methods=["GET", "POST"])
def load_index():

    if flask.request.method == 'POST':

        video_filename =  request.files['video']
        video_extension = "." + video_filename.filename.split(".")[-1]
        if video_extension not in VIDEO_FILENAME_FORMATS:
            return render_template('index.jinja2', error="El video no tiene una extensión válida.")

        server_video_filename = secure_filename(video_filename.filename)
        video_filepath = os.path.join(VIDEO_LOCAL_DIRECTORY, server_video_filename)

        video_filename.save(video_filepath)

        video_lang = request.form.get('video_lang')

        subtitles_lang = request.form.get('subtitles_lang')

        response = generate_video_subtitles(server_video_filename, video_lang, subtitles_lang)

        if response["code"] != 200:
            return render_template('index.jinja2', error="Se ha producido un error generando los subtítulos.")

        return {
            "video_filename": server_video_filename,
            "subtitles_filename": response["subtitles_filename"]
        }

    return render_template('index.jinja2', error="")

@app.route('/subtitles/<path:filename>')
def get_subtitles(filename):
    return send_from_directory(SUBTITLE_LOCAL_DIRECTORY, filename, as_attachment=True)

@app.route('/videos/<path:filename>')
def get_video(filename):
    return send_from_directory(VIDEO_LOCAL_DIRECTORY, filename, as_attachment=True)


@app.route('/show_video', methods=["GET"])
def show_video():

    video_filename = request.args.get("video_filename")
    subtitle_filename = request.args.get("subtitles_filename")

    if video_filename is None or subtitle_filename is None:

        return redirect(url_for('load_index'))

    if not os.path.exists( os.path.join(VIDEO_LOCAL_DIRECTORY, video_filename) ) \
        or not os.path.exists( os.path.join(SUBTITLE_LOCAL_DIRECTORY, subtitle_filename) ):

        return redirect(url_for('load_index'))

    return render_template(
        'show_video.jinja2',
        error="",
        video_filepath=video_filename,
        subtitle_filepath=subtitle_filename
    )