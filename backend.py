from flask import Flask, request, jsonify, send_file, render_template, session
from werkzeug.utils import secure_filename  # Import secure_filename
import subprocess
import os
import platform
import uuid
from lens import convert_to_dxf
import logging
import base64
from PIL import Image
import io
from process_face_landmarks import no_demo


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('frontend.html')  # Serve the frontend HTML

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        try:
            # Retrieve front lens image file and bridge length from the form
            front_lens_image = request.files.get('frontLensImage')
            if not front_lens_image:
                app.logger.error("No image file provided")
                return jsonify({"error": "No image file provided"}), 400

            # Generate unique IDs for the session or use the timestamp
            unique_id = uuid.uuid4().hex
            uploads_dir = 'uploads'
            outputs_dir = 'outputs'
            front_lens_image_filename = f"{unique_id}_image.jpg"
            front_lens_dxf_filename = f"{unique_id}_lens.dxf"
            front_lens_image_path = os.path.join(uploads_dir, front_lens_image_filename)
            front_lens_dxf_path = os.path.join(uploads_dir, front_lens_dxf_filename)

            os.makedirs(uploads_dir, exist_ok=True)
            os.makedirs(outputs_dir, exist_ok=True)

            # Save the image file
            front_lens_image.save(front_lens_image_path)
            app.logger.info("Saved image file")

            # Convert the image to DXF using the function from lens.py
            bbox_x, bbox_y = convert_to_dxf(front_lens_image_path, front_lens_dxf_path)
            
            session['bbox_x'] = bbox_x
            session['bbox_y'] = bbox_y
            
            
            app.logger.info("Converted image to DXF")

            # Return the generated DXF file to the client
            return send_file(os.path.abspath(front_lens_dxf_path), as_attachment=True, download_name=f"{unique_id}_lens.dxf")
        except Exception as e:
            app.logger.error(f"Failed to process request: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/upload_dxf', methods=['POST'])
def upload_dxf():
    try:
        file = request.files.get('frontLens')
        if file and allowed_file(file.filename):
            unique_id = uuid.uuid4().hex
            filename = secure_filename(file.filename)
            dxf_path = os.path.join('uploads', f"{unique_id}_{filename}")
            file.save(dxf_path)
            app.logger.info("DXF file saved")

            # Define the path for the output STL
            output_stl_path = os.path.join('outputs', f"{unique_id}_frame.stl")
            
            # get bridge length
            bridge_length = float(request.form.get('bridgeLength')) * 10
            print("bridge_length", bridge_length)
            if not bridge_length:
                app.logger.error("No bridge length provided")
                return jsonify({"error": "No bridge length provided"}), 400
            
            bbox_x = session.get('bbox_x', 'not set')
            bbox_y = session.get('bbox_y', 'not set')
            

            # Define the OpenSCAD command
            openscad_path = "/usr/local/bin/openscad" if platform.system() != 'Windows' else r"C:\Program Files\OpenSCAD\openscad.exe"
            command = [
                openscad_path,
                "-o", output_stl_path,
                "-D", f'front_view="{dxf_path}"',  # Make sure your SCAD script uses this variable
                "-D", f'bridge_length={bridge_length}',
                "-D", f'bbox_x={bbox_x}',
                "-D", f'bbox_y={bbox_y}',
                "Frame.scad"  # Path to your SCAD script
            ]

            # Execute the OpenSCAD command
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                app.logger.error(f"OpenSCAD failed: {result.stderr}")
                return jsonify({"error": f"OpenSCAD failed: {result.stderr}"}), 500

            app.logger.info("STL file generated")
            return send_file(output_stl_path, as_attachment=True)
        else:
            return jsonify({"error": "Invalid file format"}), 400
    except Exception as e:
        app.logger.error(f"Failed to process request: {str(e)}")
        return jsonify({"error": str(e)}), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'dxf'}
           
           
@app.route('/get_face_landmarks', methods=['POST'])
def get_face_landmarks():
    
    image_data = request.json.get('image')
    image_bytes = base64.b64decode(image_data.split(',')[1])
    image_pil = Image.open(io.BytesIO(image_bytes))

    bridge_width, frame_width = no_demo(image_pil)
    
    return jsonify({'nose_bridge_length': bridge_width}) # TODO return photos

if __name__ == '__main__':
    app.run(debug=True)
