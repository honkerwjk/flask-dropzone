import unittest

from flask import Flask, render_template_string, current_app, url_for

from flask_dropzone import Dropzone, allowed_file_type, _Dropzone
from flask_wtf import CSRFProtect


class ShareTestCase(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True
        self.app.secret_key = 'for test'
        dropzone = Dropzone(self.app)
        csrf = CSRFProtect(self.app)

        self.dropzone = _Dropzone

        @self.app.route('/upload')
        def upload():
            pass

        @self.app.route('/')
        def index():
            return render_template_string('''
                    {{ dropzone.load_css() }}\n{{ dropzone.create(action_view='upload') }}
                    {{ dropzone.load_js() }}\n{{ dropzone.config() }}''')

        @self.app.route('/load')
        def load():
            return render_template_string('''
                            {{ dropzone.load() }}\n{{ dropzone.create(action_view='upload') }}''')

        self.context = self.app.test_request_context()
        self.context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.context.pop()

    def test_extension_init(self):
        self.assertIn('dropzone', current_app.extensions)

    def test_load(self):
        rv = self.dropzone.load()
        self.assertIn('//cdn.bootcss.com', rv)
        self.assertIn('dropzone.min.js', rv)
        self.assertIn('dropzone.min.css', rv)
        self.assertIn('Dropzone.options.myDropzone', rv)

    def test_load_css(self):
        rv = self.dropzone.load_css()
        self.assertIn('dropzone.min.css', rv)

        rv = self.dropzone.load_css(version='5.1.0')
        self.assertIn('dropzone.min.css', rv)
        self.assertIn('5.1.0', rv)

    def test_load_js(self):
        rv = self.dropzone.load_js()
        self.assertIn('dropzone.min.js', rv)

        rv = self.dropzone.load_js(version='5.1.0')
        self.assertIn('dropzone.min.js', rv)
        self.assertIn('5.1.0', rv)

    def test_local_resources(self):
        current_app.config['DROPZONE_SERVE_LOCAL'] = True

        css_response = self.client.get('/static/dropzone/dropzone.min.css')
        js_response = self.client.get('/static/dropzone/dropzone.min.js')
        self.assertNotEqual(css_response.status_code, 404)
        self.assertNotEqual(js_response.status_code, 404)

        css_rv = self.dropzone.load_css()
        js_rv = self.dropzone.load_js()
        self.assertIn('/static/dropzone/dropzone.min.css', css_rv)
        self.assertIn('/static/dropzone/dropzone.min.js', js_rv)
        self.assertNotIn('//cdn.bootcss.com', css_rv)
        self.assertNotIn('//cdn.bootcss.com', js_rv)

    def test_config_dropzone(self):
        current_app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image'
        current_app.config['DROPZONE_MAX_FILE_SIZE'] = 5
        current_app.config['DROPZONE_MAX_FILES'] = 40
        current_app.config['DROPZONE_INPUT_NAME'] = 'test'
        current_app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image'
        current_app.config['DROPZONE_DEFAULT_MESSAGE'] = 'Drop file here'
        current_app.config['DROPZONE_REDIRECT_VIEW'] = 'index'

        rv = self.dropzone.config()
        self.assertIn('Dropzone.options.myDropzone', rv)
        self.assertIn('paramName: "test"', rv)
        self.assertIn('maxFilesize: 5', rv)
        self.assertIn('maxFiles: 40,', rv)
        self.assertIn('acceptedFiles: "%s"' % allowed_file_type['image'], rv)
        self.assertIn('dictDefaultMessage: "Drop file here"', rv)
        self.assertIn('this.on("queuecomplete", function(file) {', rv)
        self.assertIn('window.location = "/";', rv)

        rv = self.dropzone.config(redirect_url='/redirect')
        self.assertIn('this.on("queuecomplete", function(file) {', rv)
        self.assertIn('window.location = "/redirect";', rv)

    def test_create_dropzone(self):
        rv = self.dropzone.create(action=url_for('upload'))
        self.assertIn('<form action="/upload" method="post" class="dropzone" id="myDropzone"', rv)

    def test_csrf_field(self):
        rv = self.dropzone.create(action=url_for('upload'))
        self.assertNotIn('<input type="hidden" name="csrf_token"', rv)

        rv = self.dropzone.create(action=url_for('upload'), csrf=True)
        self.assertIn('<input type="hidden" name="csrf_token"', rv)

        current_app.config['DROPZONE_ENABLE_CSRF'] = True
        rv = self.dropzone.create(action=url_for('upload'))
        self.assertIn('<input type="hidden" name="csrf_token"', rv)

    def test_style_dropzone(self):
        rv = self.dropzone.style('width: 500px')
        self.assertIn('.dropzone{width: 500px}', rv)

    def test_render_template(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('//cdn.bootcss.com', data)
        self.assertIn('dropzone.min.js', data)
        self.assertIn('dropzone.min.css', data)
        self.assertIn('Dropzone.options.myDropzone', data)
        self.assertIn('<form action="/upload" method="post" class="dropzone" id="myDropzone"', data)

        response = self.client.get('/load')
        data = response.get_data(as_text=True)
        self.assertIn('//cdn.bootcss.com', data)
        self.assertIn('dropzone.min.js', data)
        self.assertIn('dropzone.min.css', data)
        self.assertIn('Dropzone.options.myDropzone', data)
        self.assertIn('<form action="/upload" method="post" class="dropzone" id="myDropzone"', data)
