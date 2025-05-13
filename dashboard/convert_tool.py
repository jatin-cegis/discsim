import streamlit as st
import chardet
import csv
import io

# Detect encoding of uploaded file
def detect_encoding(file):
    raw_data = file.read(10000)
    result = chardet.detect(raw_data)
    file.seek(0)  # Reset the file pointer after reading
    return result['encoding']

# Convert CSV content to UTF-8
def convert_to_utf8(file, detected_encoding):
    decoded = io.StringIO(file.read().decode(detected_encoding))
    reader = csv.reader(decoded)
    
    utf8_buffer = io.StringIO()
    writer = csv.writer(utf8_buffer)
    for row in reader:
        writer.writerow(row)
    
    return utf8_buffer.getvalue().encode('utf-8')  # Return as bytes

# Streamlit UI
st.title("CSV to UTF-8 Converter")
st.write("Upload a CSV file with unknown encoding. It will be auto-detected and converted to UTF-8.")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    # Detect encoding
    encoding = detect_encoding(uploaded_file)
    st.success(f"Detected encoding: {encoding}")
    
    # Convert to UTF-8
    utf8_data = convert_to_utf8(uploaded_file, encoding)

    # Provide download link
    st.download_button(
        label="Download UTF-8 CSV",
        data=utf8_data,
        file_name="converted_utf8.csv",
        mime="text/csv"
    )
