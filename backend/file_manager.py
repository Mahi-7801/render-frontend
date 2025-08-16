import os
# Disable automatic .env loading to avoid encoding issues
os.environ['FLASK_LOAD_DOTENV'] = 'false'

from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import pandas as pd
import zipfile
import io
import pymysql

app = Flask(__name__)
CORS(app)  # Add CORS support to allow requests from the frontend

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_BASE_DIR = os.path.join(BASE_DIR, 'outputs', 'gem')

def get_run_dir(run_id):
    """Constructs the output directory path for a given run_id and ensures it exists."""
    import os
    if not run_id or '..' in run_id or '/' in run_id or '\\' in run_id:
        return None, "Invalid run_id"
    run_dir = os.path.join(OUTPUTS_BASE_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)  # Always create the directory if missing
    return run_dir, None

@app.route('/')
def home():
    return "Welcome to the File Manager API!"

@app.route('/api/files/<run_id>', methods=['GET'])
def list_files(run_id):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400
    try:
        files = [f for f in os.listdir(run_dir) if f.endswith('.xlsx')]
        return jsonify(files)
    except FileNotFoundError:
        return jsonify([])

@app.route('/api/download/<run_id>/<filename>', methods=['GET'])
def download_file(run_id, filename):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400
    
    file_path = os.path.join(run_dir, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
        
    return send_file(file_path, as_attachment=True)

@app.route('/api/merge-download/<run_id>', methods=['GET'])
def merge_download(run_id):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400

    # Check if merged CSV already exists
    csv_filename = f'merged_data_{run_id}.csv'
    csv_filepath = os.path.join(run_dir, csv_filename)
    if os.path.exists(csv_filepath):
        with open(csv_filepath, 'rb') as f:
            csv_io = io.BytesIO(f.read())
        csv_io.seek(0)
        return send_file(
            csv_io,
            mimetype='text/csv',
            as_attachment=True,
            download_name=csv_filename
        )

    files = [f for f in os.listdir(run_dir) if f.endswith('.xlsx')]
    if not files:
        return "No files to merge", 404
    
    merged_df = pd.DataFrame()
    for file in files:
        df = pd.read_excel(os.path.join(run_dir, file))
        merged_df = pd.concat([merged_df, df], ignore_index=True)
    
    # Replace NaN with None for MySQL compatibility (handles all dtypes)
    merged_df = merged_df.astype(object).where(pd.notnull(merged_df), None)

    # Rename columns to match MySQL table
    column_rename_map = {
        'user name': 'user_name',
        'Bid No': 'bid_no',
        'Name of Work': 'name_of_work',
        'name of Wc': 'name_of_work',
        'category': 'category',
        'Ministry and Department': 'ministry_and_department',
        'and Depa': 'ministry_and_department',
        'Quantity': 'quantity',
        'EMD': 'emd',
        'Exemption': 'exemption',
        'Estimation Value': 'estimation_value',
        'mation Va': 'estimation_value',
        'state': 'state',
        'location': 'location',
        'Apply Mode': 'apply_mode',
        'Apply Mod': 'apply_mode',
        'Website Link': 'website_link',
        'ebsite Li': 'website_link',
        'Document Link': 'document_link',
        'Document link': 'document_link',
        'cument li': 'document_link',
        'Attachment Link': 'attachment_link',
        'Attachment link': 'attachment_link',
        'tachment l': 'attachment_link',
        'End Date': 'end_date',
    }
    merged_df.rename(columns=column_rename_map, inplace=True)

    # Remove duplicate columns, keeping only the first occurrence
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]

    # Keep only columns that match the MySQL table
    valid_columns = [
        'user_name', 'bid_no', 'name_of_work', 'category', 'ministry_and_department',
        'quantity', 'emd', 'exemption', 'estimation_value', 'state',
        'location', 'apply_mode', 'website_link', 'document_link', 'attachment_link', 'end_date'
    ]
    merged_df = merged_df[[col for col in merged_df.columns if col in valid_columns]]

    # Remove rows where all values are None/NaN
    merged_df = merged_df.dropna(how='all')
    
    # Create CSV filename and filepath
    # (already defined above)
    
    # Save merged data as CSV
    merged_df.to_csv(csv_filepath, index=False, encoding='utf-8')
    
    # --- Insert merged data into MySQL gem_data table (AWS) ---
    if not merged_df.empty:
        try:
            connection = pymysql.connect(
                host='44.244.61.85',
                port=3306,
                user='root',
                password='thanuja',
                db='Toolinformation',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            with connection:
                with connection.cursor() as cursor:
                    # Create gem_data table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS gem_data (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            user_name VARCHAR(255),
                            bid_no VARCHAR(255),
                            name_of_work TEXT,
                            category VARCHAR(255),
                            ministry_and_department VARCHAR(255),
                            quantity VARCHAR(255),
                            emd VARCHAR(255),
                            exemption VARCHAR(255),
                            estimation_value VARCHAR(255),
                            state VARCHAR(255),
                            location VARCHAR(255),
                            apply_mode VARCHAR(255),
                            website_link TEXT,
                            document_link TEXT,
                            attachment_link TEXT,
                            end_date VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """)
                    
                    # Insert data
                    cols = ','.join(f'`{col}`' for col in merged_df.columns)
                    placeholders = ','.join(['%s'] * len(merged_df.columns))
                    sql = f'INSERT INTO gem_data ({cols}) VALUES ({placeholders})'
                    for row in merged_df.itertuples(index=False, name=None):
                        cursor.execute(sql, row)
                connection.commit()
                print(f"[SUCCESS] Inserted {len(merged_df)} rows into gem_data table (AWS)")
        except Exception as e:
            print(f"[ERROR] Failed to insert merged data into gem_data (AWS): {e}")
    # --- End MySQL insert ---

    # Return CSV file for download
    with open(csv_filepath, 'rb') as f:
        csv_io = io.BytesIO(f.read())
    csv_io.seek(0)
    
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name=csv_filename
    )

@app.route('/api/delete/<run_id>/<filename>', methods=['DELETE'])
def delete_file_endpoint(run_id, filename):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400

    file_path = os.path.join(run_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'File not found'}), 404

@app.route('/api/download-all/<run_id>', methods=['GET'])
def download_all(run_id):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400
        
    files = [f for f in os.listdir(run_dir) if f.endswith('.xlsx')]
    if not files:
        return "No files to zip", 404

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w') as zf:
        for file in files:
            zf.write(os.path.join(run_dir, file), arcname=file)
    mem_zip.seek(0)
    
    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'all_data_{run_id}.zip'
    )
    
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/gem/files/<run_id>', methods=['GET'])
def gem_list_files(run_id):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400
    try:
        files = [f for f in os.listdir(run_dir) if f.endswith('.xlsx')]
        # Return file URLs for frontend
        file_objs = [{
            'name': f,
            'url': f'/api/download/{run_id}/{f}'
        } for f in files]
        return jsonify({'files': file_objs})
    except FileNotFoundError:
        return jsonify({'files': []})

@app.route('/gem/files/<run_id>/<filename>', methods=['DELETE'])
def gem_delete_file(run_id, filename):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400
    file_path = os.path.join(run_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'File not found'}), 404

@app.route('/gem/files/<run_id>/merge', methods=['POST'])
def gem_merge_files(run_id):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400
    files = [f for f in os.listdir(run_dir) if f.endswith('.xlsx')]
    if not files:
        return jsonify({'error': 'No files to merge'}), 404
    merged_df = pd.DataFrame()
    for file in files:
        df = pd.read_excel(os.path.join(run_dir, file))
        merged_df = pd.concat([merged_df, df], ignore_index=True)
    merged_filename = f'merged_data_{run_id}.xlsx'
    merged_filepath = os.path.join(run_dir, merged_filename)
    with pd.ExcelWriter(merged_filepath, engine='xlsxwriter') as writer:
        merged_df.to_excel(writer, index=False, sheet_name='MergedData')
    return jsonify({'success': True, 'merged_file': merged_filename, 'url': f'/api/download/{run_id}/{merged_filename}'})

@app.route('/api/ireps-merge-download/<run_id>', methods=['GET'])
def ireps_merge_download(run_id):
    run_dir, error = get_run_dir(run_id)
    if error:
        return jsonify({"error": error}), 400

    csv_filename = f'ireps_merged_data_{run_id}.csv'
    csv_filepath = os.path.join(run_dir, csv_filename)
    if os.path.exists(csv_filepath):
        with open(csv_filepath, 'rb') as f:
            csv_io = io.BytesIO(f.read())
        csv_io.seek(0)
        return send_file(
            csv_io,
            mimetype='text/csv',
            as_attachment=True,
            download_name=csv_filename
        )

    files = [f for f in os.listdir(run_dir) if f.endswith('.xlsx')]
    if not files:
        return "No files to merge", 404

    merged_df = pd.DataFrame()
    for file in files:
        df = pd.read_excel(os.path.join(run_dir, file))
        merged_df = pd.concat([merged_df, df], ignore_index=True)

    # Remove rows where all values are null
    merged_df = merged_df.dropna(how='all')

    # Remove duplicate rows
    merged_df = merged_df.drop_duplicates()

    # Rename columns to match tenders table
    column_rename_map = {
        'Deptt./Rly. Unit': 'dept_unit',
        'Tender No': 'tender_no',
        'Tender Title': 'tender_title',
        'Status': 'status',
        'Work Area': 'work_area',
        'Due Date/Time': 'due_datetime'
    }
    merged_df.rename(columns=column_rename_map, inplace=True)

    # Keep only the columns needed for the database
    valid_columns = ['dept_unit', 'tender_no', 'tender_title', 'status', 'work_area', 'due_datetime']
    merged_df = merged_df[[col for col in merged_df.columns if col in valid_columns]]

    # Save as CSV
    merged_df.to_csv(csv_filepath, index=False, encoding='utf-8')

    # Insert into MySQL (AWS) for IREPS 'tender' table
    if not merged_df.empty:
        try:
            connection = pymysql.connect(
                host='44.244.61.85',
                port=3306,
                user='root',
                password='thanuja',
                db='Toolinformation',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            with connection:
                with connection.cursor() as cursor:
                    # Create tender table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS tender (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            dept_unit VARCHAR(255),
                            tender_no VARCHAR(255),
                            tender_title TEXT,
                            status VARCHAR(255),
                            work_area VARCHAR(255),
                            due_datetime VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """)
                    
                    cols = ','.join(f'`{col}`' for col in merged_df.columns)
                    placeholders = ','.join(['%s'] * len(merged_df.columns))
                    sql = f'INSERT INTO tender ({cols}) VALUES ({placeholders})'
                    for row in merged_df.itertuples(index=False, name=None):
                        cursor.execute(sql, row)
                connection.commit()
                print(f"[SUCCESS] Inserted {len(merged_df)} rows into tender table (AWS)")
        except Exception as e:
            print(f"[ERROR] Failed to insert merged data into tender (AWS): {e}")

    # Return CSV file for download
    with open(csv_filepath, 'rb') as f:
        csv_io = io.BytesIO(f.read())
    csv_io.seek(0)
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name=csv_filename
    )

if __name__ == '__main__':
    # Run without debug mode to avoid .env loading issues
    app.run(port=5002, debug=False)
