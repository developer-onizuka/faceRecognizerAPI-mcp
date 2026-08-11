import os
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
UPLOAD_FOLDER = '/home/vagrant/exports'

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head><title>NFS Image Uploader</title></head>
<body style="font-family: sans-serif; margin: 40px;">
  <h2>NFS Image Uploader for MCP</h2>
  <form method="post" enctype="multipart/form-data">
    <input type="file" name="file" accept="image/*">
    <input type="submit" value="Upload">
  </form>
  <p>{{ message }}</p>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    message = ""
    if request.method == 'POST':
        if 'file' not in request.files:
            message = "No file part"
        else:
            file = request.files['file']
            if file.filename == '':
                message = "No selected file"
            else:
                filename = file.filename
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                message = f"Uploaded successfully: {filename}"
    return render_template_string(HTML_TEMPLATE, message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
