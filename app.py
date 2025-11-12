import os
import uuid
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, join_room, emit

from text_processor import TextProcessor
from dialect_mapper import DialectMapper
from tts_engine import TTSEngine
from google_tts_engine import GoogleTTSEngine
from hybrid_tts_engine import HybridTTSEngine
from vietnamese_tts_engine import VietnameseTTSEngine


app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'dev-secret'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['AUDIO_FOLDER'] = os.path.join(os.getcwd(), 'static', 'audio')

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins='*')


# In-memory state per session
sessions = {}


def _select_tts_engine():
    """Select a TTS engine, preferring ones that support Vietnamese out of the box.

    Order of preference (can be overridden via APP_TTS_ENGINE env var):
    - vietnamese (Windows SAPI/PowerShell, outputs wav)
    - google     (requires internet, outputs mp3, good Vietnamese)
    - hybrid     (tries Coqui then pyttsx3, outputs wav)
    - pyttsx3    (local SAPI5, may not have Vietnamese voices)
    """
    preferred = os.environ.get('APP_TTS_ENGINE', 'vietnamese').lower()

    if preferred == 'vietnamese':
        try:
            vn = VietnameseTTSEngine()
            if getattr(vn, 'available', False):
                # Nếu không có đúng giọng Vietnamese, ta vẫn có thể phát nhưng không phải tiếng Việt.
                # Trong trường hợp này, ưu tiên fallback sang Google nếu có để đảm bảo tiếng Việt.
                if getattr(vn, 'has_vietnamese_voice', False):
                    return vn, 'wav'
                g = GoogleTTSEngine()
                if getattr(g, 'available', False):
                    return g, 'mp3'
                # nếu không có Google, dùng vn (giọng default) để vẫn phát được
                return vn, 'wav'
        except Exception:
            pass
        # fallback chain continues below

    if preferred == 'google':
        tts = GoogleTTSEngine()
        if getattr(tts, 'available', False):
            return tts, 'mp3'
        # fallback chain
        hybrid = HybridTTSEngine()
        if getattr(hybrid, 'coqui_available', False) or getattr(hybrid, 'pyttsx3_available', False):
            return hybrid, 'wav'
        return TTSEngine(), 'wav'

    if preferred == 'hybrid':
        hybrid = HybridTTSEngine()
        if getattr(hybrid, 'coqui_available', False) or getattr(hybrid, 'pyttsx3_available', False):
            return hybrid, 'wav'
        # fallback
        g = GoogleTTSEngine()
        if getattr(g, 'available', False):
            return g, 'mp3'
        return TTSEngine(), 'wav'

    # default pyttsx3
    return TTSEngine(), 'wav'


def _emit_page(session_id: str, page_index: int):
    """Generate audio for one page and emit to the client room."""
    session = sessions.get(session_id)
    if not session:
        return False

    pages = session['pages']
    if page_index < 0 or page_index >= len(pages):
        return False

    dialect = session['dialect']
    mapper: DialectMapper = session['mapper']
    tts = session['tts']
    audio_ext = session['audio_ext']

    page_text = pages[page_index]
    mapped_text = mapper.transform_text(page_text, dialect)

    filename = f"{session_id}_page_{page_index}.{audio_ext}"
    output_path = os.path.join(app.config['AUDIO_FOLDER'], filename)

    ok = tts.generate_audio(mapped_text, output_path, dialect=dialect)
    if not ok:
        socketio.emit('error', {'message': 'Failed to generate audio'}, to=session_id)
        return False

    audio_url = f"/static/audio/{filename}"

    socketio.emit('new_page', {
        'page_number': page_index,
        'text': mapped_text,
        'audio_url': audio_url
    }, to=session_id)
    return True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    uploaded = request.files['file']
    if uploaded.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    dialect = request.form.get('dialect', 'north')

    # Save uploaded file
    session_id = str(uuid.uuid4())
    safe_name = f"{session_id}_{uploaded.filename}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    uploaded.save(save_path)

    # Process text
    processor = TextProcessor()
    full_text = processor.extract_text(save_path)
    pages = processor.split_into_pages(full_text)

    # Prepare session objects
    mapper = DialectMapper()
    tts, audio_ext = _select_tts_engine()

    sessions[session_id] = {
        'filename': uploaded.filename,
        'filepath': save_path,
        'dialect': dialect,
        'pages': pages,
        'mapper': mapper,
        'tts': tts,
        'audio_ext': audio_ext
    }

    return jsonify({
        'success': True,
        'session_id': session_id,
        'filename': uploaded.filename,
        'total_pages': len(pages)
    })


@app.route('/start_reading/<session_id>')
def start_reading(session_id: str):
    if session_id not in sessions:
        return jsonify({'success': False, 'message': 'Invalid session'}), 404

    # Initialize current page and emit first page immediately
    sessions[session_id]['current_page'] = 0
    _emit_page(session_id, 0)
    return jsonify({'success': True})


@socketio.on('join_session')
def on_join_session(data):
    session_id = data.get('session_id')
    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return
    join_room(session_id)


@socketio.on('page_finished')
def on_page_finished(data):
    session_id = data.get('session_id')
    last_page = data.get('page_number')
    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]
    next_index = int(last_page) + 1
    if next_index >= len(session['pages']):
        # End of book
        emit('new_page', {
            'page_number': last_page,
            'text': '',
            'audio_url': ''
        }, to=session_id)
        return

    session['current_page'] = next_index
    _emit_page(session_id, next_index)


@socketio.on('leave_session')
def on_leave_session(data):
    session_id = data.get('session_id')
    if not session_id or session_id not in sessions:
        return
    # Best-effort cleanup is handled in /cancel
    emit('left', {'session_id': session_id})


@app.route('/cancel/<session_id>')
def cancel_session(session_id: str):
    session = sessions.pop(session_id, None)
    if not session:
        return jsonify({'success': True})
    # Cleanup generated audio files for this session
    try:
        for root, _, files in os.walk(app.config['AUDIO_FOLDER']):
            for name in files:
                if name.startswith(f"{session_id}_page_"):
                    try:
                        os.remove(os.path.join(root, name))
                    except Exception:
                        pass
    except Exception:
        pass
    return jsonify({'success': True})


@socketio.on('change_dialect')
def on_change_dialect(data):
    session_id = data.get('session_id')
    new_dialect = data.get('dialect')
    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return
    if new_dialect not in ['north', 'central', 'south']:
        emit('error', {'message': 'Invalid dialect'})
        return
    sessions[session_id]['dialect'] = new_dialect
    emit('dialect_changed', {'dialect': new_dialect})


if __name__ == '__main__':
    # Prefer eventlet if available (as listed in requirements)
    try:
        import eventlet
        import eventlet.wsgi  # noqa: F401
        socketio.run(app, host='0.0.0.0', port=5001)
    except Exception:
        socketio.run(app, host='0.0.0.0', port=5001)


