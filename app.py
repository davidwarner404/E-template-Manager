import json
from flask import Flask, request, jsonify, redirect, url_for, render_template
import os
import imgkit
import uuid

app = Flask(__name__)

TEMPLATES_FILE = 'templates.json'

def load_templates():
    try:
        with open(TEMPLATES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_templates(templates):
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump(templates, f, indent=4)

@app.route('/upload', methods=['POST'])
def upload_template():
    templates = load_templates()
    new_template_id = str(uuid.uuid4())  # Generate a unique UUID
    new_template = {
        "id": new_template_id,
        "subject_line": request.form['subject_line'],
        "segment": request.form['segment'],
        "template": request.form['template'],
        "date": request.form['date']
    }
    
    # Generate a thumbnail image
    thumbnail_filename = f'thumbnail_{new_template_id}.jpg'
    thumbnail_path = os.path.join('static', 'thumbnails', thumbnail_filename)

    # Create a temporary HTML file to render to image
    temp_html_path = 'temp_template.html'
    with open(temp_html_path, 'w', encoding="utf-8") as temp_html_file:
        temp_html_file.write(new_template['template'])

    imgkit.from_file(temp_html_path, thumbnail_path)
    os.remove(temp_html_path)  # Clean up temporary file
    new_template['thumbnail'] = thumbnail_filename

    templates.append(new_template)
    save_templates(templates)

    return redirect(url_for('index'))

@app.route('/update/<string:template_id>', methods=['POST'])
def update_template(template_id):
    templates = load_templates()
    template = next((template for template in templates if template["id"] == template_id), None)
   
    if template is None:
        return jsonify({'error': 'Template not found'}), 404
    
    # Remove the old thumbnail if it exists
    thumbnail_path = os.path.join('static', 'thumbnails', template['thumbnail'])
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
    
    thumbnail_filename = f'thumbnail_{template_id}.jpg'
    thumbnail_path = os.path.join('static', 'thumbnails', thumbnail_filename)
    
    # Create a temporary HTML file to render to image
    temp_html_path = 'temp_template.html'
    with open(temp_html_path, 'w', encoding="utf-8") as temp_html_file:
        temp_html_file.write('<!DOCTYPE html><html><head><meta content="text/html; charset=utf-8" http-equiv="Content-Type" /><meta content="width=device-width, initial-scale=1.0" name="viewport" /><title></title></head><body style="margin: 0; padding: 1%; background-color: #f3f4f6; font-family: Arial, sans-serif; text-align: center;">' + template['template'] + '</body></html>')

    imgkit.from_file(temp_html_path, thumbnail_path)
    os.remove(temp_html_path)  # Clean up temporary file
    
    # Update the template with the new data
    template['subject_line'] = request.form['subject_line']
    template['segment'] = request.form['segment']
    template['template'] = request.form['template']
    template['date'] = request.form['date']
    template['thumbnail'] = thumbnail_filename

    # Save the updated templates
    save_templates(templates)

    return redirect(url_for('index'))

@app.route('/template/<string:template_id>', methods=['GET'])
def get_template(template_id):
    templates = load_templates()
    template = next((template for template in templates if template["id"] == template_id), None)

    if template is None:
        return jsonify({'error': 'Template not found'}), 404

    return jsonify({'template': template['template']})

@app.route('/template/<string:template_id>', methods=['DELETE'])
def delete_template(template_id):
    templates = load_templates()
    template_to_delete = next((template for template in templates if template["id"] == template_id), None)
    
    if not template_to_delete:
        return jsonify({'error': 'Template not found'}), 404

    try:
        thumbnail_path = os.path.join('static', 'thumbnails', template_to_delete['thumbnail'])
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        templates = [template for template in templates if template["id"] != template_id]
        
        save_templates(templates)
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit/<string:template_id>', methods=['GET'])
def edit_template(template_id):
    templates = load_templates()
    template = next((template for template in templates if template["id"] == template_id), None)

    if template is None:
        return jsonify({'error': 'Template not found'}), 404

    return render_template('edit.html', template=template)

@app.route('/edit/new', methods=['GET'])
def new_template():
    new_template_id = str(uuid.uuid4())  # Generate a unique UUID
    new_template = {
        "id": new_template_id,
        "subject_line": "",
        "segment": "opener",  # Default segment
        "template": "Add Your Creative Here",
        "thumbnail": "thumbnail_new.jpg",
        "date": ""  # Default date
    }

    return render_template('edit.html', template=new_template)

@app.route('/', methods=['GET'])
def index():
    templates = load_templates()
    date_filter = request.args.get('date')
    segment_filter = request.args.get('segment')

    if date_filter:
        templates = [template for template in templates if template['date'] == date_filter]

    if segment_filter:
        templates = [template for template in templates if template['segment'] == segment_filter]

    return render_template('index.html', templates=templates)

if __name__ == '__main__':
    app.run(debug=True)
